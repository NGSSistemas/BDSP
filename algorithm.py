import csv
import os
import numpy as np
import time
from copy import deepcopy
from sortedcontainers import SortedList

import config as conf
from data import Instance, BusLeg
from typing import List
from employee import Employee
from solution import Solution


class Algorithm:
    def __init__(self, instance: Instance) -> None:
        self.instance = instance

    def exhaustive_search(self, sol: Solution):
        """ Perform an exhaustive search in the neighborhood defined by assigning one leg to an other employee """
        best_solution = Solution(sol.employees)
        best_evaluation = sol.value
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


            # def best_employee(self, leg: BusLeg, employees: Employee) -> Employee:

    

class TabuSearch(Algorithm):
    def apply(self, current_solution:Solution):
        print('\n*******************************')
        print('*   TABU SEARCH (EXHAUSTIVE)  *')
        print('*******************************')
        best_solution = deepcopy(current_solution)
        # best_solution = sol.copy()
        best_objective = current_solution.value
        # current_solution = sol.copy()
        # current_solution = deepcopy(sol)
        number_of_employees = len(current_solution.employees)
        number_of_bus_legs = len(self.instance.legs)
        # tabu_list = np.zeros(shape=(number_of_employees, number_of_bus_legs))
        tabu_list = [[-conf.TABU_LENGTH for i in range(number_of_bus_legs)] for j in range(number_of_employees)] 
        start_time = time.time()
        best_T_overall = 10**(20)
        best_NT_overall = 10**(20)
        iter = 1
        while self.stopping_criteria(iter) is True:
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
                if best_T_objective < best_objective:
                    best_solution = deepcopy(current_solution)
                    best_objective = best_T_objective
                    print(f'Best Solution (Tabu)= {best_objective}')
            else:                
                # Update Tabu List
                tabu_list[best_nontabu_move[0]-1][best_nontabu_move[2].id-1] = best_nontabu_move[-1]
                current_eval = current_solution.execute_move(best_nontabu_move[0], best_nontabu_move[1], best_nontabu_move[2])
                if best_NT_objective < best_objective:
                    best_solution = deepcopy(current_solution)
                    best_objective = best_NT_objective
                    print(f'Best Solution (NonTabu) = {best_objective}')
            iter += 1
            CPU_time = time.time() - start_time
        print()
        print(f'Best Tabu objective = {best_T_overall}')
        print(f'Best NonTabu objective =', best_NT_overall)
        print()
        return best_objective, best_solution 

    def stopping_criteria(self, iteration):
        """ 1 for max number of iterations,
            2 for CPU time """
        criteria = 1
        if criteria is 1:
            if iteration < conf.MAX_ITER:
                return True
            else:
                return False
                    
                    




class ConstructionAlgorithm(Algorithm):


    def apply(self):
        legs_unassigned = self.instance.legs.copy()
        temporaryEmployees = [Employee(i + 1, self.instance) for i in range(len(legs_unassigned))]

        while len(legs_unassigned) > 0:
            leg = legs_unassigned[0]
            employee = self.bestEmployee(temporaryEmployees, leg)
            employee.bus_legs.add(leg)
            employee.evaluate()
            legs_unassigned.remove(leg)
            while True:
                next_leg = self.next_tour_leg(legs_unassigned, leg)
                if next_leg is None:
                    break
                employee.bus_legs.add(next_leg)
                employee.evaluate()
                if employee.state.MultiValue[0] == 0:
                    legs_unassigned.remove(next_leg)
                else:
                    employee.bus_legs.remove(next_leg)
                    employee.evaluate
                    break

        #     while True:
        #         next_leg = self.next_tour_leg(legs_unassigned, leg)
        #         if next_leg is None:
        #             break
        #         check = best_empl.basic_constraint(next_leg)
        #         if not check:
        #             break
        #         [times, change, ride, split, dc, start_fs, start_shift, end_ls, end_shift] = best_empl.evaluate_assign(next_leg)
        #         is_feasible = best_empl.check_feasibility(next_leg, times, split, dc)
        #         if not is_feasible:
        #             best_empl = self.best_employee(next_leg, employees)
        #             [times, change, ride, split, dc, start_fs, start_shift, end_ls, end_shift] = best_empl.evaluate_assign(next_leg)
        #             best_empl.assign_leg_to_employee(next_leg, times, change, ride, split, dc, start_fs, start_shift, end_ls, end_shift)
        #             leg = next_leg
        #             legs_unassigned.remove(next_leg)
        #             continue
        #         best_empl.assign_leg_to_employee(next_leg, times, change, ride, split, dc, start_fs, start_shift, end_ls, end_shift)
        #         legs_unassigned.remove(next_leg)    
        k = 0
        employees = []
        while temporaryEmployees[k].state.total_time > 0:
            employees.append(temporaryEmployees[k])
            k += 1

        solution = Solution(employees)
        return solution

    def bestEmployee(self, listOfEmployees: List[Employee], leg: BusLeg) -> Employee:
        """ return the employee with the lowerst objective in listOfEmployees for the leg 'leg'. """
        best_objective = 999999999
        best_key = -1
        for key, employee in enumerate(listOfEmployees):
            employee.bus_legs.add(leg)
            evaluation = employee.evaluate()
            if evaluation < best_objective:
                best_key = key
                best_objective = evaluation
            employee.bus_legs.remove(leg)
            employee.objective = employee.evaluate()
        return listOfEmployees[best_key]


    def next_tour_leg(self, legs_unassigned: list, input_leg: BusLeg) -> BusLeg:
        for leg in legs_unassigned:
            if (leg.tour == input_leg.tour):
                return leg