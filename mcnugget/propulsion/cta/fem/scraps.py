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