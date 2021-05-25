import numpy as np
import time

from data import Instance, read_solution
from algorithm import Algorithm, ConstructionAlgorithm, TabuSearch
from solution import Solution
import config as conf
from IntervalVisualizer import IntervalVisualizer



instance = Instance.read_data(conf.INSTANCE_SIZE, conf.INSTANCE_NUMBER)
algorithm = Algorithm(instance)

# ---------------------- #
# CONSTRUCTIVE ALGORITHM #
# ---------------------- # 
start = time.process_time()
initial_solution = ConstructionAlgorithm(instance).apply()
duration = time.process_time() - start
initial_solution.evaluate(instance)
print(f'Finished execution in {duration} with value {initial_solution.value}')
# initial_solution.print_objective()

# -------------- #
# READ FROM FILE #
# -------------- # 

# initial_solution = Solution.construct_solution(instance, read_solution(conf.NAME))
# initial_solution.evaluate(instance)
# solution.print_objective()



# ----------- #
# TABU SEARCH #
# ----------- # 
# Set verbosity. Verb = 0: no description
verb = 0
if verb != 0:
    print('\n****************')
    print('*   INSTANCE   *')
    print('****************')
    print('Number of legs =', len(instance.legs))
    print('Number of employees =', len(initial_solution.employees))
    print(f'Number of maximum iterations = {conf.MAX_ITER}')
    print(f'Tabu tenure = {conf.TABU_LENGTH}')
    print(f'Starting objective = {initial_solution.evaluation}')

start = time.process_time()
best_objective, best_solution = TabuSearch(instance).apply(initial_solution)
duration = time.process_time() - start
print(f'Finished execution in {duration} with value {best_objective}')

final_solution = best_solution.removeEmptyEmployees()

# final_solution.evaluate(instance)
# final_solution.print_objective()
# best_solution.print_to_file()



# intervals = result.employees
# visualizer = IntervalVisualizer(axis=IntervalVisualizer.AXIS_HOURS)
# visualizer.create(intervals, 'Results', 'tour', hover, 'tour').show()
# best_solution = best_solution.visualize_solution()

def hover(interval):
    if getattr(interval, 'tour', None) == 'S':
        string = '<b>Start work​​​​​</b><br>' \
                'Time: %{​​​​​start}​​​​​ - %{​​​​​end}​​​​​<br>'
        string = string.replace('\u200b', '')
        return string
    if getattr(interval, 'tour', None) == 'R':
        string = '<b>Ride time</b><br>' \
                'Time: %{​​​​​start}​​​​​ - %{​​​​​end}​​​​​\
                    (drive: %{​​​​​drive}​​​​​)<br>'
        string = string.replace('\u200b', '')
        return string
    if getattr(interval, 'tour', None) == 'U':
        string = '<b>Unpaid​​​​​</b><br>' \
                'Time: %{​​​​​start}​​​​​ - %{​​​​​end}​​​​​\
                    (drive: %{​​​​​drive}​​​​​)<br>'
        string = string.replace('\u200b', '')
        return string
    if getattr(interval, 'tour', None) == 'P':
        string = '<b>Paid​​​​​</b><br>' \
                'Time: %{​​​​​start}​​​​​ - %{​​​​​end} \
                    (len: %{​​​​​drive}​​​​​)​​​​​<br>'
        string = string.replace('\u200b', '')
        return string
    if getattr(interval, 'tour', None) == 'E':
        string = '<b>End work​​​​​</b><br>' \
                'Time: %{​​​​​start}​​​​​ - %{​​​​​end}<br>'
        string = string.replace('\u200b', '')
        return string

    if getattr(interval, 'tour', None) is not None:
        string = '<b>Bus leg %{​​​​​id}​​​​​</b><br>' \
                'Time: %{​​​​​start}​​​​​ - %{​​​​​end}​​​​​ \
                (drive: %{​​​​​drive}​​​​​)<br>' \
                'Tour: %{​​​​​tour}​​​​​ <br>' \
                'Positions: %{​​​​​start_pos}​​​​​ - %{​​​​​end_pos}​​​​​'
        string = string.replace('\u200b', '')
        return string
    else:
        string = '<b>%{​​​​​name}​​​​​</b><br>' \
               'Time: %{​​​​​start}​​​​​ - %{​​​​​end}​​​​​'
        string = string.replace('\u200b', '')
        return string











# best_solution = algorithm.local_search(solution)
# print('initial solution = ',solution.evaluation)
# best_solution, best_evaluation = algorithm.best_improvement(solution)
# print('best improvement = ', best_evaluation)
# best_solution.evaluate(instance)
# print(solution.move())
# best_solution.print_objective()
# solution.print_objective()


# print(best_solution)
# best_solution.evaluate(instance)
# best_solution.visualize_solution()
# visualizer.create(best_solution.employees, 'Results', 'tour', hover, 'tour').show()

# visualizer.create(output.employees, 'Results', 'tour', hover, 'tour').show()



