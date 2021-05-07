import csv
import os
import numpy as np
import time
from copy import deepcopy
from sortedcontainers import SortedList

import config as conf
from input_reading import Instance, BusLeg
from typing import List


class Employee:

    def __init__(self, id: int, instance: Instance) -> None:
        self.id = id
        self.bus_legs = SortedList()
        self.state = State()
        self.previous_state = State()
        self.instance = instance
        self.working_time = 0
        self.driving_time = 0
        self.total_time = 0
        self.end_ls = 0
        self.start_fs = 999999999999
        self.start_shift = 9999999999
        self.end_shift = 0
        self.change = 0
        self.ride = 0
        self.split = 0
        self.objective = 0
        self.previous_objective = 0
        self.working_constraints = WorkingConstraints(self)
        self.driving_constraints = DrivingConstraints(self)
        self.name = 'E' + str(id)
        self.start = 0
        self.end = 0
        self.constraints = []
        self.MultiValue = {}
        self.bus_penalty = 0
        self.drive_penalty = 0
        self.rest_penalty = 0

    def multi_value(self) -> List[int]:
        s_0 = 0
        s_1 = 0
        for con in self.constraints:
            if con.category == 1:
                s_1 += con.weight * con.value
            elif con.category == 0:
                s_0 += con.weight * con.value
        return int(s_0), int(s_1)

    def basic_constraint(self, new_leg: BusLeg) -> bool:
        """ Check two things:
            1) the last leg and new leg do not overlap
            2) If there is a tour change, the employee must have enough time to go from last pos to new pos """
        if not self.bus_legs:
            return True
        last_leg = self.bus_legs[-1]
        if last_leg.end >= new_leg.start:
            return False
        if last_leg.tour != new_leg.tour:
            pos_1 = int(last_leg.end_pos)
            pos_2 = int(new_leg.start_pos)
            number = (new_leg.start - last_leg.end - self.instance.distance_matrix[pos_1][pos_2])
            if number < 0:
                return False
        return True

    def evaluate_assign(self, leg: BusLeg) -> List:
        """ Evaluate the assignation self --> leg.
            :param leg: the bus leg we want to evaluate
            Returns:
                    - times:    -- Working time after asignation
                                -- Driving time after asignation
                                -- Total time after asignation
                    - number of split after asignation
                    - number of passive ride time after asignation
                    - number of change after asignation
        """
        if leg.start < self.start_fs:
            start_fs = leg.start
            start_shift = leg.start - self.instance.start_work[int(leg.start_pos)]
        else:
            start_fs = self.start_fs
            start_shift = self.start_shift
        if leg.end > self.end_ls:
            end_shift = leg.end + self.instance.end_work[int(leg.end_pos)]
            end_ls = leg.end
        else:
            end_ls = self.end_ls
            end_shift = self.end_shift
        total_time = end_shift - start_shift
        working_time = total_time - self.working_constraints.read_unpaid(leg)
        driving_time = self.driving_time + leg.drive
        times = [working_time, total_time, driving_time]
        ride = self.ride
        change = self.change
        split = self.split
        dc = self.driving_constraints.read_dc(leg)
        if self.bus_legs:
            last_leg = self.bus_legs[-1] 
            i = int(last_leg.end_pos)
            j = int(leg.start_pos)
            if last_leg.tour != leg.tour:
                change += 1
            if last_leg.end_pos != leg.start_pos:
                passive_ride_time = self.passive_ride(i, j)
                ride = ride + passive_ride_time
            diff = self.working_constraints.read_diff(leg)
            if (diff - self.passive_ride(i, j) >= 180):
                split += 1
        return [times, change, ride, split, dc, start_fs, start_shift, end_ls, end_shift]

    def evaluate_total_time(self, leg: BusLeg) -> float:
        if leg.start < self.start_fs:
            start_shift = leg.start - self.instance.start_work[int(leg.start_pos)]
        else:
            start_shift = self.start_shift
        if leg.end > self.end_ls:
            end_shift = leg.end + self.instance.end_work[int(leg.end_pos)]
        else:
            end_shift = self.end_shift
        total_time = end_shift - start_shift
        return total_time

    def check_feasibility(self, leg, times: List[float], split: float, dc: float) -> bool:
        """ Input: leg, [w_s, t_s, d_s]
            Returns False if the asignation (leg, self) violates the constraints.
            True otherwise
        """
        working_time = times[0]
        total_time = times[1]
        driving_time = times[2]
        break30 = self.working_constraints.read_break30(leg)
        first15 = self.working_constraints.read_first15(leg)
        if (working_time > conf.EMPLOYEE_W_MAX):
            return False
        if (total_time > conf.EMPLOYEE_T_MAX):
            return False
        if (driving_time > conf.EMPLOYEE_D_MAX):
            return False
        if (split > 2):
            return False
        if (dc >= 240):
            return False
        if break30 is False:
            return False
        if first15 is False:
            return False
        return True
   
    def assign_leg_to_employee(self, leg: BusLeg, times, change, ride, split, dc, start_fs, start_shift, end_ls, end_shift) -> None:
        self.start_fs = start_fs
        self.start_shift = start_shift
        self.end_ls = end_ls
        self.end_shift = end_shift
        self.change = change
        self.ride = ride
        self.split = split
        self.working_time = times[0]
        self.total_time = times[1]
        self.driving_time = times[2]
        self.driving_constraints.update(leg)
        self.driving_constraints.dc = dc
        self.working_constraints.update(leg)
        self.working_constraints.unpaid = self.working_constraints.read_unpaid(leg)
        self.bus_legs.append(leg)
        self.objective = self.objective_function(times, change, ride, split)

    def objective_function(self, times: list, change: float, ride: float, split: float) -> float:
        working_time = times[0]
        total_time = times[1]
        W_s = max(working_time, 390)
        result = 2*W_s + total_time + ride + 30*change + 180*split
        return result 
   
    def revert(self):
        self.objective = self.previous_objective
        self.state = self.previous_state.copy()

    def evaluate(self):
        self.previous_state = self.state
        self.state = State()
        self.previous_objective = self.objective
        self.MultiValue = {}
        if self.bus_legs:
            first_leg = self.bus_legs[0]
            start_fs = first_leg.start
            start_shift = start_fs - self.instance.start_work[(int(first_leg.start_pos))]
            last_leg = self.bus_legs[-1]
            end_ls = last_leg.end
            end_shift = end_ls + self.instance.end_work[int(last_leg.end_pos)]
            total_time = end_shift - start_shift
            driving_time = 0
            ride = 0
            change = 0
            split = 0
            split_time = 0
            bus_penalty = 0
            drive_penalty = 0
            rest_penalty = 0
            working_time = 0
            self.constraints = []
            break30 = False
            first15 = False
            # unpaid = self.state.working_constraints.evaluate()
            for leg in self.bus_legs:
                driving_time += leg.drive
            for k in range(0, len(self.bus_legs)-1):
                leg_i = self.bus_legs[k]
                leg_j = self.bus_legs[k+1] 
                i = int(leg_i.end_pos) 
                j = int(leg_j.start_pos)
                r = int(self.passive_ride(i, j))
                ride += r
                diff = leg_j.start - leg_i.end
                if (diff - r < 180):
                    diff_1 = diff - r
                else:
                    diff_1 = 0
                if diff_1 >= 30:
                    break30 = True
                if first15 is False:
                    if diff_1 >= 15 and leg_i.end - start_shift <= 6*60:
                        first15 = True
                if leg_i.tour != leg_j.tour or leg_i.end_pos != leg_j.start_pos:
                    if diff - self.instance.distance_matrix[i][j] < 0:
                        bus_penalty += - (diff - self.instance.distance_matrix[i][j])
                    elif diff <= 0:
                        bus_penalty -= diff
                    if leg_i.tour != leg_j.tour:
                        change += 1
                    if (diff - r >= 180):
                        split += 1
                        split_time += diff - r
            working_time = total_time - self.working_constraints.read_unpaid(start_shift, end_shift, end_ls) - split_time
            drive_penalty = self.driving_constraints.drive_penalty()
            rest_penalty = self.working_constraints.rest_penalty(working_time, break30, first15)
            bus_penalty_constraint = Constraints('Max(bus_chain_penalty)', 0, 1000, bus_penalty)
            self.constraints.append(bus_penalty_constraint)
            max_d = Constraints('Max(drive_time):', 0, 1000, max(driving_time - conf.EMPLOYEE_D_MAX, 0))
            self.constraints.append(max_d)
            max_s_2 = Constraints('Max(span):', 0, 1000, max(total_time - conf.EMPLOYEE_T_MAX, 0))
            self.constraints.append(max_s_2)
            max_s = Constraints('Max(span):', 1, 1, total_time)
            self.constraints.append(max_s)
            max_tour = Constraints('Max(tour_changes):', 1, 30, change)
            self.constraints.append(max_tour)
            max_ride = Constraints('Max(ride_time):', 1, 1, ride)
            self.constraints.append(max_ride)
            drive_penalty = Constraints('Max(drive_penalty):', 0, 1000, drive_penalty)
            self.constraints.append(drive_penalty)
            rest_penalty = Constraints('Max(rest_penalty):', 0, 1000, rest_penalty)
            self.constraints.append(rest_penalty)
            max_w_2 = Constraints('Max(work_time):', 0, 1000, max(working_time - conf.EMPLOYEE_W_MAX, 0))
            self.constraints.append(max_w_2)  
            max_w = Constraints('Max(work_time):', 1, 2, working_time)
            self.constraints.append(max_w)
            min_w = Constraints('Min(work_time):', 1, 2, max(conf.EMPLOYEE_W_MIN - working_time, 0))
            self.constraints.append(min_w)
            max_split = Constraints('Max(shift_split):', 1, 180, split)
            self.constraints.append(max_split)
            hard, soft = self.multi_value()  
        else:
            hard = 0
            soft = 0
        self.objective = hard + soft
        # return {0: hard, 1: soft}
        return self.objective
        
    def passive_ride(self, i: int, j: int) -> float:
        if i == j:
            return 0
        else:
            return self.instance.distance_matrix[i][j]

    def read_unpaid(self) -> float:
        sum = 0
        a = self.start_shift + 2*60
        b = self.end_shift - 2*60
        self.working_constraints.break30 = False
        self.working_constraints.center30 = False
        self.working_constraints.first15 = False

        for k in range(0, len(self.bus_legs)-1):
            leg_i = self.bus_legs[k]
            leg_j = self.bus_legs[k+1]
            i = int(leg_i.end_pos)
            j = int(leg_j.start_pos)
            r = self.passive_ride(i, j)
            diff_1 = leg_j.start - leg_i.end - r
            if diff_1 >= 15 and leg_i.end <= a + 6*60:
                self.working_constraints.first15 = True
            if diff_1 >= 3*60:
                continue
            if diff_1 >= 30:
                self.working_constraints.break30 = True
            breakEnd30 = min(b - 60, leg_j.start - r)
            breakStart30 = max(a + 60, leg_i.end)
            if breakEnd30 - breakStart30 >= 30:
                self.working_constraints.center30 = True
            breakEnd = min(b, leg_j.start - r)
            breakStart = max(a, leg_i.end)
            if breakEnd - breakStart >= 15:
                sum += breakEnd - breakStart

        if self.working_constraints.break30 is True and self.working_constraints.first15 is True:
            if self.working_constraints.center30 is True:
                return min(sum, 90)
            else:
                return min(sum, 60)
        else:
            return 0

    def _eq_(self, other):
        if isinstance(other, Employee):
            return self.id == other.id
        return False

    def __iter__(self):
        return iter(self.bus_legs)
    
    def copy(self):
        output = Employee(self.id, self.instance)
        output.bus_legs = self.bus_legs.copy()
        output.objective = self.objective
        return output


class DrivingConstraints:
    def __init__(self, employee: Employee) -> None:
        self.employee = employee
        self.dc = 0
        self.block = False
        self.b_15 = 0
        self.b_20 = 0

    def read_block(self, leg: BusLeg) -> bool:
        diff = self.employee.working_constraints.read_diff(leg)
        if (diff >= 30):
            return True
        elif (diff >= 20 and self.b_20 == 1):
            return True
        elif (diff >= 15 and self.b_15 == 2):
            return True
        return False

    def read_dc(self, leg: BusLeg) -> float:
        block = self.read_block(leg)
        if block:
            return leg.drive
        else:
            return self.dc + leg.drive

    def update(self, leg: BusLeg) -> None:
        diff = self.employee.working_constraints.read_diff(leg)
        block = self.read_block(leg)
        if block:
            self.dc = leg.drive
        else:
            self.dc += leg.drive
        if self.dc > 240:
            block = False
        else:
            block = self.read_block(leg)
        if (diff >= 20):
            self.b_20 = 1
        elif block:
            self.b_20 = 0
        if block:
            self.b_15 = 0
        elif (diff >= 15):
            self.b_15 += 1

    def drive_penalty(self) -> int:
        e = self.employee
        penalty = 0
        block = False
        b_20 = 0
        b_15 = 0
        dc = e.bus_legs[0].drive
        for k in range(len(e.bus_legs)-1):
            leg_i = e.bus_legs[k]
            leg_j = e.bus_legs[k+1]
            diff = leg_j.start - leg_i.end
            block = (diff >= 30) or (diff >= 20 and b_20 == 1) or (diff >= 15 and b_15 == 2)
            if block is True:
                dc = leg_j.drive
                b_20 = 0
                b_15 = 0
            else:
                dc += leg_j.drive
                if diff >= 20:
                    b_20 = 1
                if diff >= 15:
                    b_15 += 1
            if dc >= 4*60:
                penalty += (dc - 4*60)
        return penalty


class WorkingConstraints:
    def __init__(self, employee: Employee) -> None:
        self.employee = employee
        self.rest = 0
        self.first15 = False
        self.break30 = False
        self.center30 = True
        self.unpaid = 0

    def read_diff(self, leg: BusLeg) -> float:
        if len(self.employee.bus_legs) > 0:
            return leg.start - self.employee.bus_legs[-1].end
        else:
            return 0

    def read_diff_1(self, leg: BusLeg) -> float:
        if len(self.employee.bus_legs) > 0:
            i = int(self.employee.bus_legs[-1].end_pos)
            j = int(leg.start_pos)
            r = self.employee.passive_ride(i, j)
            diff = self.read_diff(leg)            
            if (diff - r < 180):
                return diff - r
            else:
                return 0
        else:
            return 0

    def read_diff_2(self, leg: BusLeg) -> float:
        diff_1 = self.read_diff_1(leg)
        diff_2 = diff_1
        if self.employee.bus_legs:
            last_leg = self.employee.bus_legs[-1]
            a = max(self.employee.start_shift + 120, last_leg.end)
            b = min(self.employee.end_shift - 120, leg.start)
            c = b - a
            if c >= 15:
                if last_leg.end < a:
                    diff_2 -= (a - last_leg.end)
                if leg.start > b:
                    diff_2 -= (leg.start - b)
                return diff_2
            else:
                return 0
        else:
            return 0

    def read_unpaid(self, start_shift, end_shift, end_ls) -> float:
        a = start_shift + 2*60
        b = end_shift - 2*60
        self.break30 = False
        self.center30 = False
        self.first15 = False
        unpaid = 0
        for k in range(0, len(self.employee.bus_legs)-1):
            leg_i = self.employee.bus_legs[k]
            leg_j = self.employee.bus_legs[k+1]
            i = int(leg_i.end_pos)
            j = int(leg_j.start_pos)
            r = self.employee.passive_ride(i, j)
            diff_1 = leg_j.start - leg_i.end - r
            if diff_1 >= 15 and leg_i.end <= a + 6*60:
                self.first15 = True
            if diff_1 >= 3*60:
                continue
            if diff_1 >= 30:
                self.break30 = True
            breakEnd30 = min(b - 60, leg_j.start - r)
            breakStart30 = max(a + 60, leg_i.end)
            if breakEnd30 - breakStart30 >= 30:
                self.center30 = True
            breakEnd = min(b, leg_j.start - r)
            breakStart = max(a, leg_i.end)
            if breakEnd - breakStart >= 15:
                unpaid += breakEnd - breakStart

        if self.break30 is True and self.first15 is True:
            if self.center30 is True:
                return min(unpaid, 90)
            else:
                return min(unpaid, 60)
        else:
            return 0

    def read_break30(self, leg: BusLeg) -> bool:
        unpaid = self.read_unpaid(leg)
        if self.employee.total_time - unpaid < 6*60:
            return True
        diff_1 = self.read_diff_1(leg)
        return (self.break30 or diff_1 >= 30)

    def read_first15(self, leg: BusLeg) -> bool:
        if self.first15:
            return True
        unpaid = self.read_unpaid(leg)
        total_time = self.employee.evaluate_total_time(leg)
        if total_time - unpaid < 6*60:
            return True
        if self.employee.bus_legs:
            diff_1 = self.read_diff_1(leg)
            last_leg = self.employee.bus_legs[-1]
            if (diff_1 >= 15 and (last_leg.end - self.employee.start_shift <= 60*6)):
                return True
        else:
            return False

    def evaluate_first15(self) -> bool:
        if self.first15: 
            return True
        unpaid = self.read_unpaid(leg)
        total_time = self.employee.evaluate_total_time(leg)
        if total_time - unpaid < 6*60:
            return True
        if self.employee.bus_legs:
            diff_1 = self.read_diff_1(leg)
            last_leg = self.employee.bus_legs[-1]
            if (diff_1 >= 15 and (last_leg.end - self.employee.start_shift <= 60*6)):
                return True
        else:
            return False            

    def rest_penalty(self, work_time, break30, first15) -> float:
        """ Evaluate the number of minutes that violates the rest break rules:
            - If work time is less than 6 hours --> return 0
            - If employees breaks last less than 30 minute --> return max(0, work_time - 6*60-1)
            - Else If you do less than 45 minute break --> return max(0, work_time - 9*60) 
        """
        work_time = self.employee.working_time
        penalty = 0
        if work_time < 6*60:
            return penalty
        # Check break30
        if break30 is False or first15 is False:
            k = 0
        else:
            for t in range(len(self.employee.bus_legs)-1):
                leg_i = self.employee.bus_legs[t]
                leg_j = self.employee.bus_legs[t+1]
                i = leg_i.end_pos
                j = leg_j.start_pos
                r = self.employee.passive_ride(i, j)
                diff = leg_j.start - leg_i.end
                if diff - r >= 0:
                    if diff - r >= 3*60:
                        diff_1 = 0
                    else:
                        diff_1 = diff - r
                        k += diff_1
        if k < 30:
            penalty = max(0, work_time - (6*60 - 1))
        elif k < 45:
            penalty = max(0, work_time - 9*60)
        return penalty

    def update(self, leg: BusLeg) -> None:
        self.break30 = self.read_break30(leg)
        self.first15 = self.read_first15(leg)

    # def evaluate(self):
    #     print(self.state.start_fs)
    #     # returns only the obj.function about the working constraints 


class Constraints:
    def __init__(self, name: str, category: int, weight: float, value: float) -> None:
        self.name = name
        self.category = category
        self.weight = weight
        self.value = value

    def print_con(self):
        cat = self.category
        wei = self.weight
        val = int(self.value)
        output = f'   {self.name} SingleValue({cat},{wei},{val})'
        print(output)


class State:
    def __init__(self):
        self.working_time = 0
        self.driving_time = 0
        self.total_time = 0
        self.end_ls = 0
        self.start_fs = 999999999999
        self.start_shift = 9999999999
        self.end_shift = 0
        self.change = 0
        self.ride = 0
        self.split = 0
        self.start = 0
        self.end = 0
        self.bus_penalty = 0
        self.drive_penalty = 0
        self.rest_penalty = 0
        # self.working_constraints = WorkingConstraints(self)
        # self.driving_constraints = DrivingConstraints(self)
    
    def copy(self):
        new_state = State()
        new_state.__dict__.update(self.__dict__)
        return new_state
