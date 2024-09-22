# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 17:09:24 2024

@author: natecamp
"""
        # liner cylinder
        self.model.make_solid('cylinder',r1=self.d_c/2,r2=self.d_c/2+self.t_liner,
                              x1=0,x2=self.L_cyl)
        # liner upstream throat
        # TODO: fill in r(x) lambda
        self.model.make_solid('revolve',r=lambda x: x,x1=self.L_cyl,x2=self.L_c)
        # liner downstream throat
        # TODO: fill in r(x) lambda
        self.model.make_solid('revolve',r=lambda x: x,x1=self.L_c,
                              x2=self.x_bell_start)
        # nozzle bell
        # TODO: fill in r(x) lambda
        self.model.make_solid('revolve',r=lambda x: x,x1=self.x_bell_start,
                              x2=self.L_c+self.L_n)
        # repeat the liner sections for the jacket 
        # TODO: fill in r(x) lambda
        self.model.make_solid('cylinder',r1=self.d_c/2,r2=self.d_c/2+self.t_liner,
                              x1=0,x2=self.L_cyl)
        # TODO: fill in r(x) lambda
        self.model.make_solid('revolve',r=lambda x: x,x1=self.L_cyl,x2=self.L_c)
        # TODO: fill in r(x) lambda
        self.model.make_solid('revolve',r=lambda x: x,x1=self.L_c,
                              x2=self.x_bell_start)
        # TODO: fill in r(x) lambda
        self.model.make_solid('revolve',r=lambda x: x,x1=self.x_bell_start,
                              x2=self.L_c+self.L_n)
        #test
        
        
        # set the mesh divisions
        # TODO: set list of angular divisions to line up the liner/jacket with 
        # the fins
        divs_fin_start = np.linspace(0,2*np.pi-1/self.n_fin,self.n_fin)
        divs_fin_end = divs_fin_start+self.dtheta_fin
        self.model.set_theta_divs(sorted(np.concatenate(
            divs_fin_start,divs_fin_end
            )))
        
        
        
        # get the coordinate of each node
        n_idx = 0 # node index
        for r_idx in range(self.r_numel):
            for th_idx in range(self.theta_numel):
                for x_idx in range(self.x_numel):
                    
                    
                    
    def r_liner_in(self,x):
        '''Returns the radius of the inner liner wall at the given location'''
        
        if type(x) is int or type(x) is float:
            x = [x]
        
        r = np.empty(np.size(x))
        
        for i in range(len(x)):
            xi = x[i]
            
            if xi <= self.L_cyl:
                # cylindrical section
                r[i] = self.r_c
            elif xi <= self.L_c-self.dx_cu:
                # converging chamber cone
                r[i] = self.r_c - np.tan(self.theta_con)*(xi-self.L_cyl)
            elif xi <= self.L_c:
                # upstream throat curve 
                r[i] = self.r_t + self.rcu - np.sqrt(self.rcu**2-(self.L_c-xi)**2)
            elif xi <= self.L_c+self.dx_cd:
                # downstream throat curve
                r[i] = self.r_t + self.rcd - np.sqrt(self.rcd**2-(xi-self.L_c)**2)
            elif xi <= self.L_c+self.L_n:
                # nozzle bell
                r[i] = np.polyval(self.bell_coefs,xi-self.L_c-self.dx_cd)+\
                    self.r_t+self.dr_cd
            else:
                raise ValueError(
                    'xi given to cta_fem.Model.r_liner_in exiceeds the thrust' + 
                    'chamber length')
                r[i] = np.nan
        return r
    
    