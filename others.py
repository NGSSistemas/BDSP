import csv
import os
import numpy as np
import time
from copy import deepcopy
from sortedcontainers import SortedList

import config as conf
from input_reading import Instance, BusLeg
from typing import List
from employee import Employee


class Solution:

    def __init__(self, employees: List[Employee]) -> None:
        self.employees = {employee.id: employee for employee in employees}
        self.evaluation = 0
        self.change = 0

    def copy(self):
        employees_copy = [e.copy() for e in self.employees.values()]
        output = Solution(employees_copy)
        output.evaluation = self.evaluation
        return output

    def evaluate(self, instance: Instance) -> float:
        """ Evaluate the current solution.

        :return: the sum of every employee objective
        """
        self.evaluation = 0
        for key, employee in self.employees.items():
            # self.evaluation += sum(employee.evaluate().values())
            self.evaluation += employee.evaluate()
        return self.evaluation

    def print_objective(self) -> None:
        print('\nCONSTRAINTS:')
        hard_constraints = 0
        soft_constraints = 0
        print('\nPROPERTIES:')
        for key, e in self.employees.items():
            print(' '+e.name+':')
            print('  bus_chain_penalty:', int(e.bus_penalty))
            print('  drive_time:', e.driving_time)
            print('  span:', e.total_time)
            print('  tour_changes:', e.change)
            print('  ride_time:', e.ride)
            print('  drive_penalty:', e.drive_penalty)
            print('  rest_penalty:', e.rest_penalty)
            print('  work_time:', e.working_time)
            print('  shift_split:', e.split)
        print('\nCONSTRAINTS:')
        for key, e in self.employees.items():
            hard, soft = e.multi_value()       
            e.MultiValue = {0: hard, 1: soft}
            print(f'  {e.name}: MultiValue({e.MultiValue})')
            hard_constraints += hard
            soft_constraints += soft
            for constraint in e.constraints:
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
        self.evaluation += self.change
        return self.evaluation

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
        self.evaluation -= self.change
        return self.evaluation


class Algorithm:
    def __init__(self, instance: Instance) -> None:
        self.instance = instance

    def exhaustive_search(self, sol: Solution):
        """ Perform an exhaustive search in the neighborhood defined by assigning one leg to an other employee """
        best_solution = Solution(sol.employees)
        best_evaluation = sol.evaluation
        n = len(sol.employees)
        for i in range(n-1):
            for leg in sol.employees[i].bus_legs:
                for j in range(i+1, n):
                    new_evaluation = sol.perform_swap(i, j, leg)
                    if new_evaluation < best_evaluation:
                        best_evaluation = new_evaluation
                        best_solution = sol.copy()
                    sol.revert_swap(i, j, leg)
        return best_solution, best_evaluation

    def tabu_search(self, current_solution:Solution):
        print('\n*******************************')
        print('*   TABU SEARCH (EXHAUSTIVE)  *')
        print('*******************************')
        best_solution = deepcopy(current_solution)
        # best_solution = sol.copy()
        best_objective = current_solution.evaluation
        # current_solution = sol.copy()
        # current_solution = deepcopy(sol)
        number_of_employees = len(current_solution.employees)
        number_of_bus_legs = len(self.instance.legs)
        # tabu_list = np.zeros(shape=(number_of_employees, number_of_bus_legs))
        tabu_list = [[-conf.TABU_LENGTH for i in range(number_of_bus_legs)] for j in range(number_of_employees)] 
        start_time = time.time()
        num_eval = 0
        best_T_overall = 10**(20)
        best_NT_overall = 10**(20)
        for iter in range(1, conf.MAX_ITER):
            best_NT_objective = 10**(20)
            best_T_objective = 10**(20)
            best_tabu_move = []
            best_nontabu_move = []
            for i, employee_1 in current_solution.employees.items():
                for leg in employee_1.bus_legs:
                    for j, employee_2 in current_solution.employees.items():
                        if employee_1 == employee_2:
                            continue
                        move = [i, j, leg, iter]
                        current_eval = current_solution.execute_move(i, j, leg)
                        num_eval += 1
                        if iter - tabu_list[j-1][leg.id - 1] > conf.TABU_LENGTH:
                            if current_eval < best_NT_objective:
                                best_NT_objective = current_eval
                                best_NT_overall = min(best_NT_overall, best_NT_objective)
                                best_nontabu_move = move.copy()
                        else:
                            if current_eval < best_T_objective:
                                best_T_objective = current_eval
                                best_T_overall = min(best_T_overall, best_T_objective)
                                best_tabu_move = move.copy()    
                        current_eval = current_solution.revert(i, j, leg)
            if best_T_objective < min(best_NT_objective, best_objective):
                best_T_overall = min(best_T_overall, best_T_objective)
                tabu_list[best_tabu_move[0]-1][best_tabu_move[2].id-1] = best_tabu_move[-1]
                current_eval = current_solution.execute_move(best_tabu_move[0], best_tabu_move[1], best_tabu_move[2])
                num_eval += 1
                if best_T_objective < best_objective:
                    best_solution = deepcopy(current_solution)
                    best_objective = best_T_objective
                    print(f'Best Solution (Tabu)= {best_objective}')
            else:                
                # Update Tabu List
                tabu_list[best_nontabu_move[0]-1][best_nontabu_move[2].id-1] = best_nontabu_move[-1]
                current_eval = current_solution.execute_move(best_nontabu_move[0], best_nontabu_move[1], best_nontabu_move[2])
                num_eval += 1
                if best_NT_objective < best_objective:
                    best_solution = deepcopy(current_solution)
                    best_objective = best_NT_objective
                    print(f'Best Solution (NonTabu) = {best_objective}')

        
        print(f'iteration = {iter}')
        print(f'Best Tabu objective = {best_T_overall}')
        print(f'Best NonTabu objective =', best_NT_overall)
        print(f'Number of evaluations = {num_eval}')
        print(f'CPU time = {time.time() - start_time}')



        return best_objective, best_solution 