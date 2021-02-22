from typing import Generator
import itertools
import random
import simpy


GAS_STATION_VOLUME = 200    # Liters (summary)
THRESHOLD = 10              # Threshold for calling the tank truck (in %)
FUEL_TANK_SIZE = 50         # Liters
FUEL_TANK_LEVEL = 5, 25     # Min/max levels of fuel tanks (in liters)
REFUELING_SPEED = 2         # Liters per second
TANK_TRUCK_TIME = 300       # Seconds it takes the tank truck to arrive
T_INTER = 30, 300           # Create a car every [min, max] seconds


def main():
    # Setup and start the simulation
    print("*** Gas Station Refueling ***")
    random.seed(42)

    # Create environment and start processes
    env = simpy.Environment()
    gas_station = simpy.Resource(env, capacity=2)
    fuel_pump = simpy.Container(env, GAS_STATION_VOLUME, init=GAS_STATION_VOLUME)

    env.process(gas_station_control(env, fuel_pump))
    env.process(car_generator(env, gas_station, fuel_pump))

    env.run(until=1000)

    return 0


def gas_station_control(env: simpy.Environment, fuel_pump: simpy.Container) -> Generator:
    """Periodically check the level of the *fuel_pump* and call the tank
    truck if the level falls below a threshold."""
    while True:
        if fuel_pump.level / fuel_pump.capacity * 100 < THRESHOLD:
            # We need to call the tank truck now!
            print(f"Calling tank truck at {env.now:.1f}")
            # Wait for the tank truck to arrive and refuel the station
            yield env.process(tank_truck(env, fuel_pump))

        yield env.timeout(10)   # Check every 10 seconds


def tank_truck(env: simpy.Environment, fuel_pump: simpy.Container) -> Generator:
    """Arrives at the gas station after a certain delay and refuels it."""
    yield env.timeout(TANK_TRUCK_TIME)
    print(f"Tank truck arriving at time {env.now:.1f}")
    ammount = fuel_pump.capacity - fuel_pump.level
    print(f"Tank truck refuelling {ammount:.1f} liters.")
    yield fuel_pump.put(ammount)


def car_generator(env: simpy.Environment,
                  gas_station: simpy.Resource, fuel_pump: simpy.Container) -> Generator:
    """Generate new cars that arrive at the gas station."""
    for i in itertools.count():
        yield env.timeout(random.randint(*T_INTER))
        env.process(car(env, f'Car #{i + 1}', gas_station, fuel_pump))


def car(env: simpy.Environment, name: str,
        gas_station: simpy.Resource, fuel_pump: simpy.Container) -> Generator:
    """A car arrives at the gas station for refueling.

    It requests one of the gas station's fuel pumps and tries to get the
    desired amount of gas from it. If the stations reservoir is
    depleted, the car has to wait for the tank truck to arrive.

    """
    fuel_tank_level = random.randint(*FUEL_TANK_LEVEL)
    print(f"{name} arriving at gas station at {env.now:.1f}")
    with gas_station.request() as req:
        start = env.now
        # Request one of the gas pumps
        yield req

        # Get the required amount of fuel
        liters_required = FUEL_TANK_SIZE - fuel_tank_level
        yield fuel_pump.get(liters_required)

        # The "actual" refueling process takes some time
        yield env.timeout(liters_required / REFUELING_SPEED)

        print(f"{name} finished refueling in {env.now - start:.1f} seconds")


if __name__ == '__main__':
    main()
