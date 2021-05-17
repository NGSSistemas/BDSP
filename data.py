import csv
import os
from sortedcontainers import SortedList

class Instance:
    def __init__(self, legs, distance_matrix, start_work, end_work) -> None:
        self.legs = legs
        self.distance_matrix = distance_matrix
        self.start_work = start_work
        self.end_work = end_work

    @staticmethod
    def read_data(size, number):
        os.chdir(r'./busdriver_instances')

        with open(f'realistic_{size}_{number}.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',',
                                    quoting=csv.QUOTE_NONNUMERIC)
            bus_legs = SortedList()
            line_counter = 1
            next(csv_file)
            for row in csv_reader:
                bus_legs.add(BusLeg(line_counter, int(row[0]), int(row[1]),
                                       int(row[2]), int(row[3]), int(row[4])))
                line_counter += 1

        with open(f'realistic_{size}_{number}_dist.csv') as f:
            csv_reader = csv.reader(f, delimiter=',',
                                    quoting=csv.QUOTE_NONNUMERIC)
            distance_matrix = list(csv_reader)

        with open(f'realistic_{size}_{number}_extra.csv') as csv_file_extra:
            csv_reader = csv.reader(csv_file_extra, delimiter=',',
                                    quoting=csv.QUOTE_NONNUMERIC)
            start_work = next(csv_reader)
            start_work = [int(x) for x in start_work]
            end_work = next(csv_reader)
            end_work = [int(x) for x in end_work]

        return Instance(bus_legs, distance_matrix, start_work, end_work)


class BusLeg:
    def __init__(self, id, tour, start, end, start_pos, end_pos) -> None:
        self.id = id
        self.tour = tour
        self.start = start
        self.end = end
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.start_shift = start
        self.end_shift = end
        self.name = id
        
    def __hash__(self):
        return hash(self.id)


    def __getitem__(self, item):
        return self.item
    @property
    def drive(self) -> int:
        return self.end - self.start

    def __eq__(self, other):
        if isinstance(other, BusLeg):
            return self.id == other.id

    def __lt__(self, other):
        return(self.start < other.start or (self.start == other.start and self.id < other.id))


def read_solution(name):
    os.chdir("..")
    with open(name) as csv_file:    
        csv_reader = csv.reader(csv_file, quoting=csv.QUOTE_NONNUMERIC)
        solution = list(csv_reader) 
        solution = [[int(solution[i][j]) for j in range(len(solution[0]))] for i in range(len(solution))]
    return solution