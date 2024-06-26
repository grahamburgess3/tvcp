# Imports
from __future__ import division
import pyomo.environ as pyo
from pyomo.core import Var
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt
import math
import numpy as np

# Internal imports
import fluid_flow_model as fl

# Models
class FluidModel():

    def __init__(self, data, solution, T_a, T_b):
        self.model = fl.FluidFlowModel(data, solution, T_a, T_b)
        
    def analyse(self, horizon):
        self.T = [i/365 for i in range(horizon*365)]
        self.model.analyse(self.T)
        
# Objective functions & helper func
def y0(problem):
    " linear objective function for problem Phi0"
    model = run_model(problem, {'housing' : problem.h, 'shelter' : problem.s})
    avg_unsh = sum(model.model.unsh_t)/len(model.model.unsh_t)
    avg_sh = sum(model.model.sh_t)/len(model.model.sh_t)
    return(avg_unsh + (problem.c * avg_sh))

def y1(problem):
    " nonlinear objective function for problem Phi1 and Phi2"
    model = run_model(problem, {'housing' : problem.h, 'shelter' : problem.s})
    avg_unsh_2 = sum(model.model.unsh_sq_t)/len(model.model.unsh_sq_t)
    avg_sh_2 = sum(model.model.sh_sq_t)/len(model.model.sh_sq_t)
    return(avg_unsh_2 + (problem.c * avg_sh_2))
    
def run_model(problem, solution):
    " Run model with given solution"
    model = problem.selected_model(problem.data, solution, problem.horizon_decision, problem.horizon_extra_model)
    model.analyse(problem.horizon_model)
    return(model)

# Problems
class Phi():

    objective_funcs = {'phi0' : y0,
                       'phi1' : y1,
                       'phi2' : y1}

    def __init__(self, data, modeling_options, obj, c=1):
        
        # Create Abstract Model
        self.problem = pyo.AbstractModel()

        # Attributes
        self.problem.horizon_decision = modeling_options['T_a']
        self.problem.horizon_extra_model = modeling_options['T_b']
        self.problem.horizon_model = modeling_options['T_a'] + modeling_options['T_b']
        self.problem.selected_model = modeling_options['model']
        self.problem.data = data
        self.problem.budget = data['budget']
        self.problem.costs_accomm = data['costs_accomm']
        self.problem.baseline_build = data['baseline_build']
        self.problem.c = c
        
        # Levels
        self.problem.T = pyo.RangeSet(0, int(self.problem.horizon_decision))
        self.problem.T_excl_0 = pyo.RangeSet(1, int(self.problem.horizon_decision))
        self.problem.T_excl_01 = pyo.RangeSet(2, int(self.problem.horizon_decision))
        
        # Variables
        self.problem.h = Var(self.problem.T, domain=pyo.NonNegativeReals)
        self.problem.s = Var(self.problem.T, domain=pyo.NonNegativeReals)

        # Objective function
        self.problem.OBJ = pyo.Objective(rule=self.objective_funcs[obj])

    def set_initial_conditions(self):
        self.problem.init_h = pyo.Constraint(rule=init_conditions_h)
        self.problem.init_s = pyo.Constraint(rule=init_conditions_s)
    
    def add_total_budget_constraint(self):
        self.problem.BUDGET = pyo.Constraint(rule=budget_constraint)

    def add_annual_budget_constraint_check(self):
        self.problem.budget_annual_check = pyo.Constraint(self.problem.T_excl_0,rule=budget_constraint_checked_annually)
    
    def add_baseline_build_constraint(self):
        self.problem.h_base = pyo.Constraint(self.problem.T_excl_0,rule=min_house_build)
        self.problem.s_base = pyo.Constraint(self.problem.T_excl_0,rule=min_shelter_build)

    def add_housing_increase(self):
        self.problem.h_increase = pyo.Constraint(self.problem.T_excl_0, rule = h_up)
        self.problem.h_rate_increase = pyo.Constraint(self.problem.T_excl_01, rule = h_rate_up)
            
    def add_shelter_increase_decrease(self, shelter_mode):
        self.problem.T_shelter_first = pyo.RangeSet(1, shelter_mode)
        self.problem.T_shelter_second = pyo.RangeSet(shelter_mode+1, self.problem.horizon_decision)
        self.problem.s_increase = pyo.Constraint(self.problem.T_shelter_first, rule = s_up)
        self.problem.s_decrease = pyo.Constraint(self.problem.T_shelter_second, rule = s_down)
        self.problem.s_not_too_low = pyo.Constraint(self.problem.T_shelter_second, rule = s_not_below_init)

    def solve(self, solver):
        self.opt=SolverFactory(solver)
        self.instance=self.problem.create_instance()
        self.results=self.opt.solve(self.instance)
        self.h_opt=[self.instance.h[i].value for i in range(len(self.instance.h))]
        self.s_opt=[self.instance.s[i].value for i in range(len(self.instance.s))]
        self.print_results()
        self.plot_opt({'housing' : self.h_opt, 'shelter' : self.s_opt})

    def print_results(self):
        print('------- Optimal solution -------')
        print('Housing capacity at end of each year: ' + str([round(i,2) for i in self.h_opt[1:]]))
        print('Shelter capacity at the end of each year: ' + str([round(i,2) for i in self.s_opt[1:]]))
        print('Optimal objective val: ' + str(round(self.instance.OBJ(),2)))

    def plot_opt(self, solution):
        # run model at optimal
        model = self.problem.selected_model(self.problem.data, solution, self.problem.horizon_decision, self.problem.horizon_extra_model)
        model.analyse(self.problem.horizon_model)

        # plotting
        x = [i/365 for i in range(self.problem.horizon_model*365)]
        fig, ax = plt.subplots()
        ymax = max(model.model.h_t + model.model.sh_t + model.model.unsh_t)
        ax.plot(x, model.model.h_t, color = 'green')
        ax.plot(x, model.model.sh_t, color = 'orange')
        ax.plot(x, model.model.unsh_t, color = 'red')
        ax.set(xlabel='$d/365$ (Time in years)', ylabel='Number of people',
               title='Number of people housed/sheltered/unsheltered')
        ax.legend(["$h_d$", "$s_d$", "$u_d$"], loc="lower right")
        ax.grid()
        ax.set_ylim(0,ymax*1.05)
        plt.show()

class Phi0(Phi):
    def __init__(self, data, modeling_options, obj, c):
        super(Phi0, self).__init__(data, modeling_options, obj, c)
        self.set_initial_conditions()
        self.add_total_budget_constraint()
        self.add_baseline_build_constraint()

    def solve(self, solver):
        super(Phi0, self).solve(solver)

class Phi1(Phi0):
    def __init__(self, data, modeling_options, obj, c):
        super(Phi1, self).__init__(data, modeling_options, obj, c)

    def solve(self, solver):
        super(Phi1, self).solve(solver)

class Phi2(Phi):
    def __init__(self, data, modeling_options, obj, c, shelter_mode):
        super(Phi2, self).__init__(data, modeling_options, obj, c)
        self.set_initial_conditions()
        self.add_annual_budget_constraint_check()
        self.add_housing_increase()
        self.add_shelter_increase_decrease(shelter_mode)

    def solve(self, solver):
        super(Phi2, self).solve(solver)

# constraint funcs
def init_conditions_h(problem):
    return problem.h[0]==problem.data['initial_capacity']['housing']

def init_conditions_s(problem):
    return problem.s[0]==problem.data['initial_capacity']['shelter']

def budget_constraint(problem):
    costs = 0
    for t in range(problem.horizon_decision):
        costs += (problem.h[t+1]-problem.h[t]) * problem.costs_accomm['housing']
        costs += (problem.s[t+1]-problem.s[t]) * problem.costs_accomm['shelter']
    return costs <= problem.budget

def budget_constraint_checked_annually(problem,t):
    costs = 0
    for s in range(1,t+1):
        costs += (problem.h[s]-problem.h[s-1]) * problem.costs_accomm['housing']
        costs += (problem.s[s]-problem.s[s-1]) * problem.costs_accomm['shelter']  
    return costs <= problem.budget
    
def min_house_build(problem,t):
    return problem.h[t] - problem.h[t-1] >= problem.data['baseline_build']

def min_shelter_build(problem,t):
    return problem.s[t] - problem.s[t-1] >= problem.data['baseline_build']

def h_up(problem,t):
    return (problem.h[t] >= problem.h[t-1])

def h_rate_up(problem,t):
    return (problem.h[t]-problem.h[t-1] >= problem.h[t-1]-problem.h[t-2])

def s_up(problem,t):
    return (problem.s[t] >= problem.s[t-1])

def s_down(problem,t):
    return (problem.s[t] <= problem.s[t-1])

def s_not_below_init(problem,t):
    return (problem.s[t] >= problem.s[0])