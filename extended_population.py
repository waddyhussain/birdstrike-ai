import csv
import os
import shutil

from neat.checkpoint import *
from neat.population import *


# Class that extends functionality of NEAT's own Population object
# Allows exiting training when needed
# Automatically saves population and best genome
class ExtendedPopulation(Population):
    def __init__(self, config, name, initial_state=None):
        super().__init__(config, initial_state)
        self.running = True
        self.name = name
        self.filepath = f"ai-instances/{name}"
        self.checkpoint = Checkpointer(None, None, f"{self.filepath}/gen-")

    def run(self, fitness_function, n=None):
        """
                Runs NEAT's genetic algorithm for at most n generations.  If n
                is None, run until solution is found or extinction occurs.

                The user-provided fitness_function must take only two arguments:
                    1. The population as a list of (genome id, genome) tuples.
                    2. The current configuration object.

                The return value of the fitness function is ignored, but it must assign
                a Python float to the `fitness` member of each genome.

                The fitness function is free to maintain external state, perform
                evaluations in parallel, etc.

                It is assumed that fitness_function does not modify the list of genomes,
                the genomes themselves (apart from updating the fitness member),
                or the configuration object.
                """

        k = 0
        while (n is None or k < n) and self.running:
            k += 1

            self.reporters.start_generation(self.generation)

            # Temporary pointer to population before evaluating genomes
            temp = self.population

            # Evaluate all genomes using the user-provided function.
            fitness_function(list(iteritems(self.population)), self.config)

            # Gather and report statistics.
            best = None
            for g in itervalues(self.population):
                if best is None or g.fitness > best.fitness:
                    best = g
            self.reporters.post_evaluate(self.config, self.population, self.species, best)

            # Track the best genome ever seen.
            if self.best_genome is None or best.fitness > self.best_genome.fitness:
                self.best_genome = best

            # Reset progress for current generation and exit
            if not self.running:
                self.population = temp
                break

            if not self.config.no_fitness_termination:
                # End if the fitness threshold is reached.
                fv = self.fitness_criterion(g.fitness for g in itervalues(self.population))
                if fv >= self.config.fitness_threshold:
                    self.reporters.found_solution(self.config, self.generation, best)
                    break

            # Create the next generation from the current generation.
            self.population = self.reproduction.reproduce(self.config, self.species,
                                                          self.config.pop_size, self.generation)

            # Check for complete extinction.
            if not self.species.species:
                self.reporters.complete_extinction()

                # If requested by the user, create a completely new population,
                # otherwise raise an exception.
                if self.config.reset_on_extinction:
                    self.population = self.reproduction.create_new(self.config.genome_type,
                                                                   self.config.genome_config,
                                                                   self.config.pop_size)
                else:
                    raise CompleteExtinctionException()

            # Divide the new population into species.
            self.species.speciate(self.config, self.population, self.generation)

            self.reporters.end_generation(self.config, self.population, self.species)

            self.generation += 1

        if self.config.no_fitness_termination:
            self.reporters.found_solution(self.config, self.generation, self.best_genome)

        # Update index to link ai instance with
        newfile = []
        # Read index and add new link for current file
        with open("ai-instances/index.csv") as csvfile:
            reader = csv.reader(csvfile)
            exists = False
            for row in reader:
                try:
                    row_name = row[0].lower()
                except IndexError:
                    row_name = None

                if row_name == self.name.lower():
                    try:
                        shutil.rmtree(self.filepath)
                    except FileNotFoundError:
                        pass

                    newfile.append([self.name, f"{self.filepath}/gen-{self.generation}"])
                    exists = True
                else:
                    newfile.append(row)

            if not exists:
                newfile.append([self.name, f"{self.filepath}/gen-{self.generation}"])

        newfile = filter(None, newfile)

        # Write new index file
        with open("ai-instances/index.csv", "w") as csvfile:
            writer = csv.writer(csvfile)
            for row in newfile:
                writer.writerow(row)

        # Save population and best genome to file
        try:
            os.mkdir(self.filepath)
        except FileExistsError:
            pass
        finally:
            self.checkpoint.save_checkpoint(self.config, self.population, self.species, self.generation)
            with open(f"{self.filepath}/best.pickle", "wb") as file:
                pickle.dump(self.best_genome, file)

    # Creates ExtendedPopulation object from normal Population object
    @classmethod
    def from_population(cls, population, name):
        return cls(population.config, name, (population.population, population.species, population.generation))


# Return list of instance names stored in index
def get_instance_names():
    with open("ai-instances/index.csv") as csvfile:
        reader = csv.reader(csvfile)
        names = []
        for row in reader:
            try:
                names.append(row[0])
            except IndexError:
                pass

        names = [name for name in filter(None, names)]

        return names


# Delete save data and entry in index of given name
def delete_instance(name):
    path = f"ai-instances/{name}"
    index = "ai-instances/index.csv"

    # Delete any save data that exists
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass

    # End function if the instance isn't in the index file
    if name.lower() not in [instance.lower() for instance in get_instance_names()]:
        return

    # Remove the instance's entry from the index file
    newfile = []
    with open(index) as file:
        reader = csv.reader(file)
        for row in reader:
            try:
                row_name = row[0]
            except IndexError:
                continue

            if row_name.lower() == name.lower():
                continue

            newfile.append(row)

    with open(index, 'w') as file:
        writer = csv.writer(file)
        for row in newfile:
            writer.writerow(row)


# Rename given instance with new name
def rename_instance(name, new_name):
    index = "ai-instances/index.csv"
    path = f"ai-instances/{name}"
    newpath = f"ai-instances/{new_name}"

    try:
        # Rename the folder containing the save data if it exists
        os.rename(path, newpath)
    except FileNotFoundError:
        # If no save data exists, delete the instance's entry from the index file and print error message
        print("No save data exists for this instance. Deleting from list...")
        delete_instance(name)
        return

    if name.lower() in [instance.lower() for instance in get_instance_names()]:
        # Rename instance's entry in the index file
        newfile = []
        with open(index) as file:
            reader = csv.reader(file)
            for row in reader:
                try:
                    row_name = row[0]
                except IndexError:
                    continue

                if row_name.lower() == name.lower():
                    newfile.append([new_name, f"{newpath}{row[1][len(path):]}"])
                else:
                    newfile.append(row)

        with open(index, 'w') as file:
            writer = csv.writer(file)
            for row in newfile:
                writer.writerow(row)
    else:
        # Print error message if there is no entry for the instance in the index file
        print(f"No record found for {name}. Failed to rename")
