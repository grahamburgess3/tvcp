import numpy as np
import math

class FluidFlowModel():

    def __init__(self, data, solution, T_a, T_b):
        """
        Initialise instance of fluid flow model - continuous approximation of M(t)/M/s(t) model
        
        Parameters
        ----------
        data : dict : includes 'initial_demand', 'service_mean', 'arrival_rates'
        solution : dict(list) : includes annual annual capacity for 'housing' and 'shelter' (including initial)
        T_a : int : decision horizon in days
        T_b : int : additional modelling horizon in days

        """
        self.T_a = T_a
        self.T_b = T_b
        self.X_0 = data['initial_demand']     
        self.h = solution['housing']
        self.s = solution['shelter']
        self.h_t = [solution['housing'][0]]
        self.sh_t = [solution['shelter'][0]]
        self.unsh_t = [self.X_0 - solution['housing'][0] - solution['shelter'][0]]
        self.sh_sq_t = [solution['shelter'][0]**2]
        self.unsh_sq_t = [self.unsh_t[0]**2]
        self.mu0 = 1/(data['service_mean']['housing']) # daily service rate for individual housing unit
        self.lambda_t = data['arrival_rates'] # daily arrival rate

    def analyse(self, T):
        """
        Evaluate Q performance measures for all times in T
        
        Parameters
        ----------
        T : list[float] : times (in units of days) to evaluate queue size

        """
        
        for t in T[1:len(T)]:
            unsh, sh, h, unsh_sq, sh_sq = self.evaluate_queue_size(t)
            self.unsh_t.append(unsh)
            self.unsh_sq_t.append(unsh**2)
            self.sh_t.append(sh)
            self.sh_sq_t.append(sh_sq)
            self.h_t.append(h)
    
    def evaluate_queue_size(self, t):
        """
        Evaluate number unsheltered at time t
        
        Parameters
        ----------
        t : float : time (in days)

        Returns
        -------
        u_t : float : number unsheltered at time t

        """

        # init quantities
        fluid_in = 0
        fluid_out = 0

        # how much beyond decision horizon to model
        diff = t - self.T_a
        t_temp = min(t,self.T_a) # to start by modelling up to decision horizon
        T = math.floor(t_temp) # number of years passed

        # house and shelter numbers
        if t_temp<self.T_a:        
            houses = self.h[T] + (t_temp%1)*(self.h[T+1]-self.h[T])
            shelters = self.s[T] + (t_temp%1)*(self.s[T+1]-self.s[T])
        else:
            houses = self.h[self.T_a]
            shelters = self.s[self.T_a]

        # add complete years
        for yr in range(T):
            fluid_in += self.lambda_t[yr]*365
            fluid_out += self.mu0 * (self.h[yr]+self.h[yr+1])/2
            
        # add fractional year
        if (t_temp % 1 > 0):
            fluid_in += (t_temp % 1) * self.lambda_t[T]*365
            fluid_out += (t_temp % 1) * self.mu0 * (self.h[T] + (self.h[T+1]-self.h[T]) * 0.5 * (t_temp%1))

        # model beyond the decision horizon
        if diff > 0:
            T = math.floor(diff) # number of years passed
            for yr in range(T):
                fluid_in += self.lambda_t[yr+self.T_a]*365
                fluid_out += self.mu0 * self.h[self.T_a]
                
            # add fractional year
            fluid_in += (diff % 1) * self.lambda_t[T+self.T_a]*365
            fluid_out += (diff % 1) * self.mu0 * self.h[self.T_a]

        # calculate queue lengths (expected values)
        unsh = self.X_0 + fluid_in - fluid_out - houses - shelters
        sh = shelters
        h = houses

        # calculate squared queue lengths (expected vals)
        unsh_sq = unsh**2
        sh_sq = sh**2
        
        # return
        return unsh, sh, h, unsh_sq, sh_sq