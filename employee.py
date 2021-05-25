
import numpy as np
from sortedcontainers import SortedList

import config as conf
from data import Instance, BusLeg
from typing import List


class Employee:

    def __init__(self, id: int, instance: Instance) -> None:
        self.id = id
        self.bus_legs = SortedList()
        self.state = State(self)
        self.previous_state = State(self)
        self.instance = instance
        self.objective = 0
        self.previous_objective = 0
        self.working_constraints = WorkingConstraints(self)
        self.driving_constraints = DrivingConstraints(self)
        self.name = 'E' + str(id)


    # def assignLegToEmployee(self, leg):

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
        """ Evaluate the objective function of the current employee  """
        self.previous_state = self.state
        self.previous_objective = self.objective
        self.state = State(self)
        self.objective = self.state.evaluate()
        return self.objective
        
    def passive_ride(self, i: int, j: int) -> float:
        if i == j:
            return 0
        else:
            return self.instance.distance_matrix[i][j]


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

    def read_unpaid(self) -> float:
        a = self.employee.state.start_shift + 2*60
        b = self.employee.state.end_shift - 2*60
        self.break30 = False
        self.center30 = False
        self.first15 = False
        unpaid = 0
        for key, leg in enumerate(self.employee.bus_legs[:-1]):
            leg_i = self.employee.bus_legs[key]
            leg_j = self.employee.bus_legs[key+1]
            i = int(leg_i.end_pos)
            j = int(leg_j.start_pos)
            ride = self.employee.passive_ride(i, j)
            diff = leg_j.start - leg_i.end
            if diff - ride >= 180:
                diff_1 = 0
            else:
                diff_1 = diff - ride
            if diff_1 >= 15 and leg_i.end <= a + 6*60:
                self.first15 = True
            if diff_1 >= 30:
                self.break30 = True
            breakEnd30 = min(b - 60, leg_j.start - ride)
            breakStart30 = max(a + 60, leg_i.end)
            if breakEnd30 - breakStart30 >= 30:
                self.center30 = True
            breakEnd = min(b, leg_j.start - ride)
            breakStart = max(a, leg_i.end)
            if breakEnd - breakStart >= 15:
                unpaid += breakEnd - breakStart
        
        if self.break30 is False or self.first15 is False:
            return 0

        if self.center30 is True:
            unpaid = min(unpaid, 90)
        else:
            unpaid = min(unpaid, 60)

        return unpaid

    def rest_penalty(self) -> float:
        """ Evaluate the number of minutes that violates the rest break rules:
            - If work time is less than 6 hours --> return 0
            - If employees breaks last less than 30 minute --> return max(0, work_time - 6*60-1)
            - Else If you do less than 45 minute break --> return max(0, work_time - 9*60) 
        """
        rest_penalty = 0
        k = 0
        if self.employee.state.work_time < 6*60:
            return rest_penalty
        # Check break30
        if self.break30 is False or self.first15 is False:
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
            rest_penalty = max(0, self.employee.state.work_time - (6*60 - 1))
        elif k < 45:
            rest_penalty = max(0, self.employee.state.work_time - 9*60)
        
        return rest_penalty

    def update(self, leg: BusLeg) -> None:
        self.break30 = self.read_break30(leg)
        self.first15 = self.read_first15(leg)

    def evaluate(self):
        """ Return the objective function value of the working constraints """
        a = self.employee.state.start_shift + 2*60
        b = self.employee.state.end_shift - 2*60
        self.break30 = False
        self.center30 = False
        self.first15 = False
        unpaid = 0
        rest_penalty = 0
        k = 0
        for key, leg in enumerate(self.employee.bus_legs[:-1]):
            leg_i = self.employee.bus_legs[key]
            leg_j = self.employee.bus_legs[key+1]
            i = int(leg_i.end_pos)
            j = int(leg_j.start_pos)
            ride = self.employee.passive_ride(i, j)
            diff = leg_j.start - leg_i.end
            if diff - ride >= 180:
                diff_1 = 0
            else:
                diff_1 = diff - ride
            if diff_1 >= 15 and leg_i.end <= a + 6*60:
                self.first15 = True
            if diff_1 >= 30:
                self.break30 = True
            breakEnd30 = min(b - 60, leg_j.start - ride)
            breakStart30 = max(a + 60, leg_i.end)
            if breakEnd30 - breakStart30 >= 30:
                self.center30 = True
            breakEnd = min(b, leg_j.start - ride)
            breakStart = max(a, leg_i.end)
            if breakEnd - breakStart >= 15:
                unpaid += breakEnd - breakStart
        
        if self.break30 is False or self.first15 is False:
            unpaid = 0

        if self.center30 is True:
            unpaid = min(unpaid, 90)
        else:
            unpaid = min(unpaid, 60)
        if self.employee.state.work_time < 6*60:
            return rest_penalty
        # Check break30
        if self.break30 is False or self.first15 is False:
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
            rest_penalty = max(0, self.employee.state.work_time - (6*60 - 1))
        elif k < 45:
            rest_penalty = max(0, self.employee.state.work_time - 9*60)
        
        return unpaid, rest_penalty


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
    def __init__(self, employee: Employee):
        self.employee = employee
        self.MultiValue = {}
        self.constraints = []
        self.work_time = 0
        self.drive_time = 0
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

    def evaluate(self):
        if not self.employee.bus_legs:
           return 0
        evaluation = 0
        self.bus_penalty = 0
        self.drive_time = 0
        self.change = 0
        self.split = 0
        split_time = 0
        self.ride = 0
        first_leg = self.employee.bus_legs[0]
        self.start_shift = first_leg.start - self.employee.instance.start_work[first_leg.start_pos]
        last_leg = self.employee.bus_legs[-1]
        self.end_shift = last_leg.end + self.employee.instance.end_work[last_leg.end_pos]
        self.total_time = self.end_shift - self.start_shift
        for leg in self.employee.bus_legs:
            self.drive_time += leg.drive
        for key, leg in enumerate(self.employee.bus_legs[:-1]):
            leg_i = self.employee.bus_legs[key]
            leg_j = self.employee.bus_legs[key+1]
            i = int(leg_i.end_pos)
            j = int(leg_j.start_pos)
            r = int(self.employee.passive_ride(i, j))
            self.ride += r
            diff = leg_j.start - leg_i.end
            if (diff - r < 180):
                diff_1 = diff - r
            else:
                diff_1 = 0
            if leg_i.tour != leg_j.tour or leg_i.end_pos != leg_j.start_pos:
                if diff - self.employee.instance.distance_matrix[i][j] < 0:
                    self.bus_penalty += - (diff - self.employee.instance.distance_matrix[i][j])
                elif diff <= 0:
                    self.bus_penalty -= diff
                if leg_i.tour != leg_j.tour:
                    self.change += 1
                if (diff - r >= 180):
                    self.split += 1
                    split_time += diff - r
        unpaid = self.employee.working_constraints.read_unpaid()
        # unpaid, rest_penalty = self.employee.working_constraints.evaluate()
        self.work_time = self.total_time - unpaid - split_time
        self.drive_penalty = self.employee.driving_constraints.drive_penalty()
        # self.rest_penalty = rest_penalty
        self.rest_penalty = self.employee.working_constraints.rest_penalty()

        ## Constraint adding:
        self.constraints.append(Constraints('Max(bus_chain_penalty)', 0, 1000, self.bus_penalty))
        self.constraints.append(Constraints('Max(drive_time):', 0, 1000, max(self.drive_time - conf.EMPLOYEE_D_MAX, 0)))
        self.constraints.append(Constraints('Max(span):', 0, 1000, max(self.total_time - conf.EMPLOYEE_T_MAX, 0)))
        self.constraints.append(Constraints('Max(span):', 1, 1, self.total_time))
        self.constraints.append(Constraints('Max(tour_changes):', 1, 30, self.change))
        self.constraints.append(Constraints('Max(ride_time):', 1, 1, self.ride))
        self.constraints.append(Constraints('Max(drive penalty):', 0, 1000, self.drive_penalty))
        self.constraints.append(Constraints('Max(rest penalty):', 0, 1000, self.rest_penalty))
        self.constraints.append(Constraints('Max(work_time):', 0, 1000, max(self.work_time - conf.EMPLOYEE_W_MAX, 0)))  
        self.constraints.append(Constraints('Max(work_time):', 1, 2, self.work_time))
        self.constraints.append(Constraints('Min(work_time):', 1, 2, max(conf.EMPLOYEE_W_MIN - self.work_time, 0)))
        self.constraints.append(Constraints('Max(shift_split):', 1, 180, self.split))
        # output = self.finalSum()
        hard, soft = self.finalSum()
        self.MultiValue = {0: hard, 1: soft}
        return hard + soft

    def finalSum(self) -> List[int]:
        s_0 = 0
        s_1 = 0
        for con in self.constraints:
            if con.category == 1:
                s_1 += con.weight * con.value
            elif con.category == 0:
                s_0 += con.weight * con.value
        return int(s_0), int(s_1)

    def copy(self):
        employee_copy = self.employee.copy()
        new_state = State(employee_copy)
        new_state.__dict__.update(self.__dict__)
        return new_state
