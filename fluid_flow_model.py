import numpy as np

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
        self.X_0 = data['initial_demand']     
        self.h = self.get_daily_capacity(solution['housing'], T_a, T_b)
        self.s = self.get_daily_capacity(solution['shelter'], T_a, T_b)
        self.s_sq = [x**2 for x in self.s] # (num sheltered)^2 over time
        self.u = [self.X_0 - solution['housing'][0] - solution['shelter'][0]] # initial number unsheltered
        self.u_sq = [self.u[0]**2] #  initial (num unsheltered)^2
        self.mu0 = 1/(data['service_mean']['housing']*365) # daily service rate for individual housing unit
        self.lambda_t = list(np.repeat(data['arrival_rates'],365)) # daily arrival rate

    def get_daily_capacity(self, solution, T_a, T_b):

        """
        Initialise instance of fluid flow model - fluid limit of M(t)/M/s(t) model
        
        Parameters
        ----------
        solution : list : capacity at the end of each subsequent year
        T_a : int : decision horizon in days
        T_b : int : additional modelling horizon in days

        Returns
        -------
        daily : list : daily capacity levels for decision horizon + extra modelling horizon

        """
        
        annual = list(solution)
        diffs = list(np.repeat([(annual[i+1] - annual[i])/365 for i in range(int(T_a/365))],365))
        daily = [solution[0] + sum(diffs[0:i]) for i in range(1,len(diffs)+1)] + [list(solution)[-1]]*T_b
        return daily

    def analyse(self, T):
        """
        Evaluate Q performance measures for all times in T
        
        Parameters
        ----------
        T : list[float] : times (in units of days) to evaluate queue size

        """

        for t in T[1:len(T)]:
            unsh = self.evaluate_queue_size(t)
            self.u.append(unsh)
            self.u_sq.append(unsh**2)
    
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

        # compute u_t
        u_t = self.X_0 + sum(self.lambda_t[0:t]) - sum(self.h[0:t])*self.mu0 - self.h[t] - self.s[t]
        
        # return
        return u_t