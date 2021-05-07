import math

INSTANCE_SIZE = 3
INSTANCE_NUMBER = "0"

# INSTANCE_SIZE = "5"
# INSTANCE_NUMBER = "0"

# INSTANCE_SIZE = "10"
# INSTANCE_NUMBER = "1"


# INSTANCE_SIZE = "100"
# INSTANCE_NUMBER = "50"


# NAME = f'realistic_{INSTANCE_SIZE}_{INSTANCE_NUMBER}_solution.csv' 
NAME = f'TabuSearchResult.csv'
# NAME = f'TabuSearchResultStored.csv'

# NAME = f'solution.csv'   
# NAME = f'small_solution_2.csv'     
    # NAME = f'mid_solution_2.csv'   

EMPLOYEE_D_MAX = 9*60
EMPLOYEE_W_MAX = 10*60
EMPLOYEE_W_MIN = int(6.5*60)
EMPLOYEE_T_MAX = 14*60

MAX_ITER = 100
TABU_LENGTH = math.floor(math.sqrt(MAX_ITER))