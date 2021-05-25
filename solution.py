import csv
import os
import numpy as np
import time
from sortedcontainers import SortedList

import config as conf
from data import Instance, BusLeg
from typing import List
from employee import Employee


class Solution:

    def __init__(self, employees: List[Employee]) -> None:
        self.employees = {employee.id: employee for employee in employees}
        self.value = 0
        self.change = 0

    def copy(self):
        employees_copy = [e.copy() for e in self.employees.values()]
        output = Solution(employees_copy)
        output.value = self.value
        return output

    def evaluate(self, instance: Instance) -> float:
        """ Evaluate the current solution.

        :return: the sum of every employee objective
        """
        self.value = 0
        for key, employee in self.employees.items():
            # self.evaluation += sum(employee.evaluate().values())
            self.value += employee.evaluate()
        return self.value

    def print_objective(self) -> None:
        print('\nCONSTRAINTS:')
        hard_constraints = 0
        soft_constraints = 0
        print('\nPROPERTIES:')
        for key, e in self.employees.items():
            print(' '+e.name+':')
            print('  bus_chain_penalty:', int(e.state.bus_penalty))
            print('  drive_time:', e.state.drive_time)
            print('  span:', e.state.total_time)
            print('  tour_changes:', e.state.change)
            print('  ride_time:', e.state.ride)
            print('  drive_penalty:', e.state.drive_penalty)
            print('  rest_penalty:', e.state.rest_penalty)
            print('  work_time:', e.state.work_time)
            print('  shift_split:', e.state.split)
        print('\nCONSTRAINTS:')
        for key, e in self.employees.items():
            print(f'  {e.name}: MultiValue({e.state.MultiValue})')
            hard_constraints += e.state.MultiValue[0]
            soft_constraints += e.state.MultiValue[1]
            for constraint in e.state.constraints:
                constraint.print_con()
        MultiValue = {0: hard_constraints, 1: soft_constraints}
        print(f' \nvalue: MultiValue:({MultiValue})')

    def print_to_file(self) -> None:
        """ print the solution into a .csv file
        The output format is a binary matrix n x l where:
            n is the number of employee
            l is the number of bus legs (ordered by start time)
            the element (i,j) is 1 if leg j is assigned to employee i, 0 otherwise.
        """
        l = len(self.employees[1].instance.legs)
        n = len(self.employees)
        data = [[0 for i in range(l)] for j in range(n)]
        with open('TabuSearchResult.csv', mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for key, employee in self.employees.items():
                for leg in self.employees[1].instance.legs:
                    if leg in employee.bus_legs:
                        j = self.employees[1].instance.legs.index(leg)
                        data[key-1][j] = 1
                writer.writerow(data[key-1])
        csv_file.close()

    def visualize_solution(self):
        break_counter = 0
        for i, e in self.employees.items():
            a = e.start_shift + 2*60
            b = e.end_shift - 2*60
            if e.working_constraints.break30 is True and e.working_constraints.first15 is True:
                for k in range(0, len(e.bus_legs)-1):
                    leg_i = e.bus_legs[k]
                    leg_j = e.bus_legs[k+1]
                    i = int(leg_i.end_pos)
                    j = int(leg_j.start_pos)
                    r = e.passive_ride(i, j)
                    if r > 0:
                        Ride = BusLeg(None, 'R', leg_j.start - r, leg_j.start, 0, 0)
                        e.bus_legs.append(Ride)
                    # leg_j.start -= r 
                    if leg_i.end < a:
                        end_break = int(min(a, leg_j.start - r))
                        if end_break - leg_i.end  >= 15:
                            Paid = BusLeg(None, 'P', leg_i.end, end_break, 0, 0) 
                            e.bus_legs.append(Paid)
                    if leg_j.start > b:
                        start_break = max(b, leg_i.end)
                        if leg_j.start - start_break >= 15:
                            Paid = BusLeg(None, 'P', start_break, leg_j.start, 0, 0) 
                            e.bus_legs.append(Paid)
                    if a < leg_i.end  and leg_j.start - r < b:
                        end_break = int(min(a, leg_j.start - r))
                        if end_break - leg_i.end >= 15:
                            Unpaid = BusLeg(None, 'U', leg_i.end, end_break, 0, 0) 
                            e.bus_legs.append(Unpaid)

            if e.start_shift != e.start_fs:
                start = BusLeg(None, 'S', e.start_shift, e.start_fs, 0, 0)
                start.name = 'Start'
                e.bus_legs.insert(0, start)
            if e.end_shift != e.end_ls:
                end = BusLeg(None, 'E', e.end_ls, e.end_shift, 0, 0)
                end.name = 'End'
                e.bus_legs.append(end)
  
    @staticmethod
    def construct_solution(instance: Instance, matrix: List):
        """ Construct a solution.
        
        :param matrix: a binary nxl matrix
        :return solution: return a list of n employees
        """
        employees = []    
        for i in range(len(matrix)):
            employees.append(Employee(i+1, instance))
            for col in range(len(matrix[0])):
                if matrix[i][col] == 1:
                    employees[i].bus_legs.add(instance.legs[col])    
        employees = sorted(employees, key=lambda x: x.bus_legs[0].start)        
        for i, employee in enumerate(employees):
            employee.id = i + 1
            employee.name = 'E' + str(i+1)
        solution = Solution(employees)
        return solution

    def execute_move(self, i: int, j: int, leg: BusLeg) -> float:
        """ Execute the move  [e_i, e_j, leg].

        :param i:   Index of first employee e1
        :param j:   Index of second employee e2
        :param leg: Leg that is removed from i, and added to j 
        :return: the new evaluation after executing the move
        if new_e1, new_e2 are the new employeers, the change is
            change = - z(old_e1) - z(old_e2) + z(new_e1) + z(new_e2)
        Hence, the new evaluation is
            newEval = oldEval + change
        """
        self.employees[i].bus_legs.remove(leg)
        self.employees[j].bus_legs.add(leg)
        self.change = -(self.employees[i].objective + self.employees[j].objective)
        # self.change += sum(self.employees[i].evaluate().values())
        # self.change += sum(self.employees[j].evaluate().values())
        self.change += self.employees[i].evaluate()
        self.change += self.employees[j].evaluate()
        self.value += self.change
        return self.value

    def revert(self, i: int, j: int, leg: BusLeg) -> None:
        """ Revert the move [e_i, e_j, leg] previously done.

        :param i:   Index of first employee e1
        :param j:   Index of second employee e2
        :param leg: Leg that is added to i, and removed to j        
        :return: the old evaluation, after reverting the move
        """

        self.employees[i].bus_legs.add(leg)
        self.employees[i].revert()
        self.employees[j].bus_legs.remove(leg)
        self.employees[j].revert()
        self.value-= self.change
        return self.value

    def removeEmptyEmployees(self):
        """ Remove all the employees tha has empty bus legs """
        employees = []
        for key, employee in self.employees.items():
            if employee.objective > 0:
                employees.append(employee)
        outputSolution = Solution(employee)
        return outputSolution
        