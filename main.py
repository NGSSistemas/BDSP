import numpy as np

from input_reading import Instance
from input_reading import read_solution
from others import Algorithm
from others import Solution
import config as conf
from IntervalVisualizer import IntervalVisualizer

visualizer = IntervalVisualizer(axis=IntervalVisualizer.AXIS_HOURS)


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


instance = Instance.read_data(conf.INSTANCE_SIZE, conf.INSTANCE_NUMBER)

# result = Algorithm(instance).constructive_algorithm()
# result.evaluate(instance)
# result = result.visualize_solution()
# result.print_solution()
# intervals = result.employees
# visualizer.create(intervals, 'Results', 'tour', hover, 'tour').show()


matrix = read_solution(conf.NAME)
# matrix = np.array(matrix)
# solution = Solution(matrix)
solution = Solution.construct_solution(instance, matrix)
solution.evaluate(instance)
solution.print_objective()
# solution.visualize_solution()
algorithm = Algorithm(instance)
# Set verbosity. Verb = 0: no description 
verb = 0
if verb != 0:
    print('\n****************')
    print('*   INSTANCE   *')
    print('****************')
    print('Number of legs =', len(instance.legs))
    print('Number of employees =', len(solution.employees))
    print(f'Number of maximum iterations = {conf.MAX_ITER}')
    print(f'Tabu tenure = {conf.TABU_LENGTH}')
    print(f'Starting objective = {solution.evaluation}')

# best_objective, best_solution = algorithm.tabu_search(solution)
# best_solution.evaluate(instance)
# best_solution.print_objective()
# best_solution.print_to_file()
# best_solution = best_solution.visualize_solution()












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



