"""Exact episode-aware G13 replay semantics, including aligned force labels.

The source-to-destination provenance is recorded in the training audit.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Mapping, Sequence

import numpy as np
import torch


class EpisodeReplayBuffer:
    def __init__(self, capacity: int, observation_dim: int, action_dim: int,
                 horizon: int, batch_size: int, *, seed: int = 0) -> None:
        self.capacity = int(capacity)
        self.observation_dim = int(observation_dim)
        self.action_dim = int(action_dim)
        self.horizon = int(horizon)
        self.batch_size = int(batch_size)
        if min(self.capacity, self.horizon, self.batch_size) <= 0:
            raise ValueError("capacity, horizon, and batch_size must be positive")
        self._episodes = deque()
        self._size = 0
        self._rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return self._size

    @property
    def num_sequences(self) -> int:
        return sum(max(0, episode["actions"].shape[0] - self.horizon + 1)
                   for episode in self._episodes)

    def can_sample(self) -> bool:
        return self.num_sequences > 0

    def add_episode(self, observations: Sequence[np.ndarray], actions: Sequence[np.ndarray],
                    rewards: Sequence[float], terminated: Sequence[bool]) -> None:
        observations_array = np.asarray(observations, dtype=np.float32)
        actions_array = np.asarray(actions, dtype=np.float32)
        rewards_array = np.asarray(rewards, dtype=np.float32)
        terminated_array = np.asarray(terminated, dtype=np.float32)
        length = actions_array.shape[0]
        if observations_array.shape != (length + 1, self.observation_dim):
            raise ValueError("observations must contain one more 22-D item than actions")
        if actions_array.shape != (length, self.action_dim):
            raise ValueError("actions have wrong shape")
        if rewards_array.shape != (length,) or terminated_array.shape != (length,):
            raise ValueError("rewards and terminated must contain one value per action")
        if not all(np.all(np.isfinite(array)) for array in
                   (observations_array, actions_array, rewards_array)):
            raise FloatingPointError("Cannot store non-finite replay data")
        if length > self.capacity:
            start = length - self.capacity
            observations_array = observations_array[start:]
            actions_array = actions_array[start:]
            rewards_array = rewards_array[start:]
            terminated_array = terminated_array[start:]
            length = self.capacity
        episode = {"observations": observations_array.copy(),
                   "actions": actions_array.copy(), "rewards": rewards_array.copy(),
                   "terminated": terminated_array.copy()}
        while self._episodes and self._size + length > self.capacity:
            self._size -= self._episodes.popleft()["actions"].shape[0]
        self._episodes.append(episode)
        self._size += length

    def state_dict(self) -> dict[str, Any]:
        return {"capacity": self.capacity, "observation_dim": self.observation_dim,
                "action_dim": self.action_dim, "horizon": self.horizon,
                "batch_size": self.batch_size, "episodes": list(self._episodes),
                "size": self._size, "rng_state": self._rng.bit_generator.state}

    def load_state_dict(self, state: Mapping[str, Any]) -> None:
        expected = (self.observation_dim, self.action_dim, self.horizon)
        received = (int(state["observation_dim"]), int(state["action_dim"]), int(state["horizon"]))
        if received != expected:
            raise ValueError(f"Replay dimensions/horizon {received} do not match {expected}")
        self._episodes = deque(state["episodes"])
        self._size = int(state["size"])
        self._rng.bit_generator.state = state["rng_state"]


class G13ReplayBuffer(EpisodeReplayBuffer):
    """Store next-interval 22-substep maximum force per executed action."""

    def add_episode(self, observations, actions, rewards, terminated, forces) -> None:
        force_array = np.asarray(forces, dtype=np.float32)
        if (force_array.shape != (len(actions),) or not np.all(np.isfinite(force_array))
                or np.any(force_array < 0)):
            raise ValueError("G13 force targets must be finite nonnegative and one per action")
        super().add_episode(observations, actions, rewards, terminated)
        stored = self._episodes[-1]
        stored["forces"] = force_array[-len(stored["actions"]):].copy()

    def sample(self, device: torch.device):
        counts = np.asarray([max(0, episode["actions"].shape[0] - self.horizon + 1)
                             for episode in self._episodes], dtype=np.int64)
        total = int(counts.sum())
        if total == 0:
            raise RuntimeError("G13 replay lacks a complete sequence")
        cumulative = np.cumsum(counts)
        obs = np.empty((self.horizon + 1, self.batch_size, self.observation_dim), dtype=np.float32)
        actions = np.empty((self.horizon, self.batch_size, self.action_dim), dtype=np.float32)
        rewards = np.empty((self.horizon, self.batch_size, 1), dtype=np.float32)
        terminated = np.empty_like(rewards)
        forces = np.empty_like(rewards)
        episodes = list(self._episodes)
        sampled = self._rng.integers(0, total, size=self.batch_size)
        for batch_index, global_index in enumerate(sampled):
            episode_index = int(np.searchsorted(cumulative, global_index, side="right"))
            previous = 0 if episode_index == 0 else int(cumulative[episode_index - 1])
            start = int(global_index - previous)
            end = start + self.horizon
            episode = episodes[episode_index]
            if "forces" not in episode:
                raise RuntimeError("G13 replay episode lacks force targets")
            obs[:, batch_index] = episode["observations"][start:end + 1]
            actions[:, batch_index] = episode["actions"][start:end]
            rewards[:, batch_index, 0] = episode["rewards"][start:end]
            terminated[:, batch_index, 0] = episode["terminated"][start:end]
            forces[:, batch_index, 0] = episode["forces"][start:end]
        return tuple(torch.as_tensor(array, device=device)
                     for array in (obs, actions, rewards, terminated, forces))
