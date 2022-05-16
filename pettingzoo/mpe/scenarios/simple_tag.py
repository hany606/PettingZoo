import numpy as np

from .._mpe_utils.core import Agent, Landmark, World
from .._mpe_utils.scenario import BaseScenario
from copy import deepcopy


class Scenario(BaseScenario):
    def make_world(self, num_good=1, num_adversaries=3, num_obstacles=2):
        world = World()
        # set any world properties first
        world.dim_c = 2
        num_good_agents = num_good
        num_adversaries = num_adversaries
        num_agents = num_adversaries + num_good_agents
        num_landmarks = num_obstacles
        # add agents
        world.agents = [Agent() for i in range(num_agents)]
        for i, agent in enumerate(world.agents):
            agent.adversary = True if i < num_adversaries else False
            base_name = "adversary" if agent.adversary else "agent"
            base_index = i if i < num_adversaries else i - num_adversaries
            agent.name = f"{base_name}_{base_index}"
            agent.collide = True
            agent.silent = True
            agent.size = 0.075 if agent.adversary else 0.05
            agent.accel = 3.0 if agent.adversary else 4.0
            agent.max_speed = 1.0 if agent.adversary else 1.3
        # add landmarks
        world.landmarks = [Landmark() for i in range(num_landmarks)]
        for i, landmark in enumerate(world.landmarks):
            landmark.name = "landmark %d" % i
            landmark.collide = True
            landmark.movable = False
            landmark.size = 0.2
            landmark.color = np.array([0.25, 0.25, 0.25])
            landmark.boundary = False
        
        world.landmarks += self.set_boundaries(world)
        return world


    def set_boundaries(self, world):
        boundary_list = []
        
        # landmark_size = 1#2
        # edge = 1.5 + landmark_size
        # num_landmarks = int(edge * 2 / landmark_size)
        # for x_pos in [-edge, edge]:
        #     for i in range(num_landmarks):
        #         landmark = Landmark()
        #         landmark.state.p_pos = np.array([x_pos, -1.5 + i * landmark_size])
        #         boundary_list.append(landmark)

        # for y_pos in [-edge, edge]:
        #     for i in range(num_landmarks):
        #         landmark = Landmark()
        #         landmark.state.p_pos = np.array([-1.5 + i * landmark_size, y_pos])
        #         boundary_list.append(landmark)

        landmark_size = 2
        edge = 1.5 + landmark_size
        s_landmark_size = 0.94975/2
        s_edge = 1.75
        landmark = Landmark()
        landmark.state.p_pos = np.array([0, -edge])
        boundary_list.append(landmark)
        landmark = Landmark()
        landmark.state.p_pos = np.array([0, edge])
        boundary_list.append(landmark)
        landmark = Landmark()
        landmark.state.p_pos = np.array([edge, 0])
        boundary_list.append(landmark)
        landmark = Landmark()
        landmark.state.p_pos = np.array([-edge, 0])
        boundary_list.append(landmark)

        landmark = Landmark()
        landmark.state.p_pos = np.array([s_edge, -s_edge])
        boundary_list.append(landmark)
        landmark = Landmark()
        landmark.state.p_pos = np.array([-s_edge, -s_edge])
        boundary_list.append(landmark)
        landmark = Landmark()
        landmark.state.p_pos = np.array([-s_edge,s_edge])
        boundary_list.append(landmark)
        landmark = Landmark()
        landmark.state.p_pos = np.array([s_edge, s_edge])
        boundary_list.append(landmark)



        for i, l in enumerate(boundary_list):
            l.name = "boundary %d" % i
            l.collide = True
            l.movable = False
            l.boundary = True
            l.color = np.array([0.75, 0.75, 0.75])
            size = landmark_size
            # ---------------
            if(i >= 4):
                size = s_landmark_size
            # ---------------
            l.size = size
            l.state.p_vel = np.zeros(world.dim_p)

        return boundary_list


    def reset_world(self, world, np_random, specific_pos=None):
        # random properties for agents
        for i, agent in enumerate(world.agents):
            agent.color = (
                np.array([0.35, 0.85, 0.35])
                if not agent.adversary
                else np.array([0.85, 0.35, 0.35])
            )
            # random properties for landmarks
        # for i, landmark in enumerate(world.landmarks):
        #     landmark.color = np.array([0.25, 0.25, 0.25])

        # set random initial states
        for agent in world.agents:
            if(specific_pos is not None and agent.name in list(specific_pos.keys())):
                agent.state.p_pos = deepcopy(specific_pos[agent.name])
            else:
                agent.state.p_pos = np_random.uniform(-1, +1, world.dim_p)
            # print(agent.name, agent.state.p_pos)
            agent.state.p_vel = np.zeros(world.dim_p)
            agent.state.c = np.zeros(world.dim_c)
        for i, landmark in enumerate(world.landmarks):
            if not landmark.boundary:
                if(specific_pos is not None and "landmark" in list(specific_pos.keys()) and i < len(specific_pos["landmark"])):
                    landmark.state.p_pos = deepcopy(specific_pos["landmark"][i])
                else:
                    landmark.state.p_pos = np_random.uniform(-0.9, +0.9, world.dim_p)
                # print(f"Landmark {i}: {landmark.state.p_pos}")
                landmark.state.p_vel = np.zeros(world.dim_p)

    def benchmark_data(self, agent, world):
        # returns data for benchmarking purposes
        if agent.adversary:
            collisions = 0
            for a in self.good_agents(world):
                if self.is_collision(a, agent):
                    collisions += 1
            return collisions
        else:
            return 0

    def is_collision(self, agent1, agent2):
        delta_pos = agent1.state.p_pos - agent2.state.p_pos
        dist = np.sqrt(np.sum(np.square(delta_pos)))
        dist_min = agent1.size + agent2.size
        return True if dist < dist_min else False

    # return all agents that are not adversaries
    def good_agents(self, world):
        return [agent for agent in world.agents if not agent.adversary]

    # return all adversarial agents
    def adversaries(self, world):
        return [agent for agent in world.agents if agent.adversary]

    def reward(self, agent, world):
        # Agents are rewarded based on minimum agent distance to each landmark
        main_reward = (
            self.adversary_reward(agent, world)
            if agent.adversary
            else self.agent_reward(agent, world)
        )
        return main_reward

    def agent_reward(self, agent, world):
        # Agents are negatively rewarded if caught by adversaries
        rew = 0
        shape = False
        adversaries = self.adversaries(world)
        if (
            shape
        ):  # reward can optionally be shaped (increased reward for increased distance from adversary)
            for adv in adversaries:
                rew += 0.1 * np.sqrt(
                    np.sum(np.square(agent.state.p_pos - adv.state.p_pos))
                )
        if agent.collide:
            for a in adversaries:
                if self.is_collision(a, agent):
                    rew -= 10

        # agents are penalized for exiting the screen, so that they can be caught by the adversaries
        def bound(x):
            if x < 0.9:
                return 0
            if x < 1.0:
                return (x - 0.9) * 10
            return min(np.exp(2 * x - 2), 10)

        for p in range(world.dim_p):
            x = abs(agent.state.p_pos[p])
            rew -= bound(x)

        return rew

    def adversary_reward(self, agent, world):
        # Adversaries are rewarded for collisions with agents
        rew = 0
        shape = False
        agents = self.good_agents(world)
        adversaries = self.adversaries(world)
        if (
            shape
        ):  # reward can optionally be shaped (decreased reward for increased distance from agents)
            for adv in adversaries:
                rew -= 0.1 * min(
                    np.sqrt(np.sum(np.square(a.state.p_pos - adv.state.p_pos)))
                    for a in agents
                )
        if agent.collide:
            for ag in agents:
                for adv in adversaries:
                    if self.is_collision(ag, adv):
                        rew += 10
        # agents are penalized for exiting the screen, so that they can be caught by the adversaries
        def bound(x):
            if x < 1.1:
                return 0
            if x < 1.2:
                return (x - 1.1) * 10
            return min(np.exp(2 * x - 2), 10)
        for p in range(world.dim_p):
            x = abs(agent.state.p_pos[p])
            rew -= bound(x)
        return rew

    def observation(self, agent, world):
        # get positions of all entities in this agent's reference frame
        entity_pos = []
        for entity in world.landmarks:
            if not entity.boundary:
                entity_pos.append(entity.state.p_pos - agent.state.p_pos)
        # communication of all other agents
        comm = []
        other_pos = []
        other_vel = []
        for other in world.agents:
            if other is agent:
                continue
            comm.append(other.state.c)
            other_pos.append(other.state.p_pos - agent.state.p_pos)
            if not other.adversary:
                other_vel.append(other.state.p_vel)
        return np.concatenate(
            [agent.state.p_vel]
            + [agent.state.p_pos]
            + entity_pos
            + other_pos
            + other_vel
        )
