# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 19:30:13 2024

@author: natecamp
"""

import numpy as np
import pandas as pd
import thermal_fem as tfem

class Model:
    '''A class representing a finite element thermal model of a thrust chamber.
    
    '''
    
    def __init__(self, input_fname):
        self.input_fname = input_fname
        # read in the input sheet
        input_tbl = pd.read_excel(input_fname,sheet_name='inputs',
                                  usecols=['variable','value'])
        # assign the variables of the input table to the object
        for v in range(input_tbl.shape[0]):
            setattr(self, input_tbl.loc[v,'variable'],input_tbl.loc[v,'value'])
        # initialize the finite element model
        self.model = tfem.Model()
        # fuel properties
        self.fuel_props = Fluid(self.fuel)
        # calculate other geometry values
        self.calc_geometry()
        # setup the model
        self.setup()
        # convergence tolerance
        self.tol = 0.1 # K

            
    def setup(self):
        # the mesh and contacts will remain constant through the solving
        # generate the mesh
        self.generate_mesh()
        # build the contacts
        self.build_contacts()
        # set initial coolant temperatures
        self.init_cooling()
        # set the convection boundaries
        self.set_boundaries()
        
    def solve(self):

        max_Tc = self.get_max_Tc()

        # solve the wall temepratures
        self.model.solve()
        
        is_converged = False
        while not is_converged:
            prev_max_Tc = max_Tc
            # calculate the coolant temepratures
            self.update_cooling()
            # get the new max temperature after the regen was updated
            max_Tc = self.get_max_Tc()
            
            # update the convection based on the new coolant temepratures
            self.set_boundaries()
            # resolve the wall temperatures
            self.model.solve()
            # determine convergence based on how much the maximum fuel 
            # temperature changed in the iteration
            is_converged = abs(max_Tc-prev_max_Tc) < self.tol
            print('max_Tc:',max_Tc,' converged:',is_converged)
                
        # TODO: check that the model is converged, ideally based on the heat 
    
    def generate_mesh(self):
        '''Builds the mesh.'''
        # call make_solid to make the bodies

        # set the number of divisions in each solid
        self.model.set_r_numel(3)
        self.model.set_theta_numel(3)
        self.model.set_x_numel(20)
                        
        # fin
        # only do half of fin and channel for symmetry
        self.model.make_solid('revolve',r1=lambda x: self.r_liner_out(x),
                              r2=lambda x: self.r_jacket_in(x),
                              x1=0,x2=self.L_c+self.L_n,
                              theta1=lambda x: np.full(x.shape,0),
                              theta2=lambda x: self.dtheta_fin(x)/2,
                              material='C18150',name='fin')
        # liner beneath fin
        self.model.make_solid('revolve',r1=lambda x: self.r_liner_in(x),
                              r2=lambda x: self.r_liner_out(x),
                              x1=0,x2=self.L_c+self.L_n,
                              theta1=lambda x: np.full(x.shape,0),
                              theta2=lambda x: self.dtheta_fin(x)/2,
                              material='C18150',name='liner_on_fin')
        # jacket above fin
        self.model.make_solid('revolve',r1=lambda x: self.r_jacket_in(x),
                              r2=lambda x: self.r_jacket_out(x),
                              x1=0,x2=self.L_c+self.L_n,
                              theta1=lambda x: np.full(x.shape,0),
                              theta2=lambda x: self.dtheta_fin(x)/2,
                              material='C18150',name='jacket_on_fin')

        # do halfway between fins for symmetry
        # liner between fins
        self.model.make_solid('revolve',r1=lambda x: self.r_liner_in(x),
                          r2=lambda x: self.r_liner_out(x),
                          x1=0,x2=self.L_c+self.L_n,
                          theta1=lambda x: -self.dtheta_chan(x)/2,
                          theta2=lambda x: np.full(x.shape,0),
                          material='C18150',name='liner_in_chan')

        # jacket between fins
        self.model.make_solid('revolve',r1=lambda x: self.r_jacket_in(x),
                          r2=lambda x: self.r_jacket_out(x),
                          x1=0,x2=self.L_c+self.L_n,
                          theta1=lambda x: -self.dtheta_chan(x)/2,
                          theta2=lambda x: np.full(x.shape,0),
                          material='C18150',name='jacket_in_chan')
            
        # now the mesh should be complete
            

    def build_contacts(self):
        # contacts
        self.model.make_contact('liner_on_fin','fin')
        self.model.make_contact('fin','jacket_on_fin')
        self.model.make_contact('jacket_on_fin','jacket_in_chan')
        self.model.make_contact('liner_on_fin','liner_in_chan')
            
    def set_boundaries(self):
        # convective boundaries
        # first yeet the old ones
        self.model.clear_convections()
        # outer liner to fuel
        self.model.make_convection('liner_in_chan','r+',
                                   h=lambda x: self.get_hc_liner(x),
                                   T=lambda x: self.get_Tc(x))
        # -theta side of fins
        self.model.make_convection('fin','theta-',
                                   h=lambda x: self.get_hc_liner(x),
                                   T=lambda x: self.get_Tc(x))
        # +theta side of fins is insulated because it is the symmetry plane of 
        # the fins. being insulated means there's no heat transfer from one 
        # channel to another which is a good assumption

        # inner jacket to fuel
        self.model.make_convection('jacket_in_chan','r-',
                                   h=lambda x: self.get_hc_jacket(x),
                                   T=lambda x: self.get_Tc(x))
        # hot gas to inner liner
        self.model.make_convection('liner_in_chan','r-',
                                   h=lambda x: self.get_hg(x),
                                   T=lambda x: self.get_Taw(x))
        self.model.make_convection('liner_on_fin','r-',
                                   h=lambda x: self.get_hg(x),
                                   T=lambda x: self.get_Taw(x))
        # outer jacket to ambient
        self.model.make_convection('jacket_in_chan','r+',
                                   h=lambda x: self.h_amb,
                                   T=lambda x: self.T_amb)
        self.model.make_convection('jacket_on_fin','r+',
                                   h=lambda x: self.h_amb,
                                   T=lambda x: self.T_amb)
    
    def calc_geometry(self):
        '''Sets geometry parameters derived from the primary inputs.
        
        Calculated values
        self.Lcyl
        self.x_bell_start
        self.r_t
        self.r_c
        self.r_e
        self.bell_coefs
        '''

        # radius of the inner throat
        r_t = self.d_t/2
        # radius at the nozzle exit
        r_e = self.d_e/2
        # radius at the chamber
        r_c = self.d_c/2
        # radius of curvature of the upstream/downstream throat
        rcu = self.rcu_norm*r_t
        rcd = self.rcd_norm*r_t
        # length and width of the upstream/downstream throat curves
        dx_cu = rcu*np.sin(self.theta_con)
        dr_cu = rcu*(1-np.cos(self.theta_con))
        dx_cd = rcd*np.sin(self.theta_i)
        dr_cd = rcd*(1-np.cos(self.theta_i))
        
        # length of chamber cylinder
        L_cyl = self.L_c - dx_cu - (r_c-r_t-dr_cu)/np.tan(self.theta_con)
        
        # solve the bell
        Lb = self.L_n-dx_cu
        Ab = np.array([
            [0,0,0,1],
            [Lb**3,Lb**2,Lb,1],
            [0,0,1,0],
            [3*Lb**2,2*Lb,1,0]
            ])
        self.bell_coefs = np.linalg.solve(Ab,
                [0,r_e-r_t-dr_cd,np.tan(self.theta_i),np.tan(self.theta_e)])

       
        # now put variables in the object
        self.Lb = Lb
        self.r_t = r_t
        self.r_c = r_c
        self.r_e = r_e
        self.L_cyl = L_cyl
        self.dr_cd = dr_cd
        self.dx_cd = dx_cd
        self.dr_cu = dr_cu
        self.dx_cu = dx_cu
        self.rcu = rcu
        self.rcd = rcd

        # ----------- do some regen stuff -------------        
        # regen x values
        self.xc = np.linspace(self.x_fuel_in,0,self.Nc)

        # find all of the cross section areas
        self.Acs = 1/2*self.dtheta_chan(self.xc)*(
            self.r_jacket_in(self.xc)**2-self.r_liner_out(self.xc)**2)
        
        # hydraulic diameter (4A/P)
        # the jacket surface is actually a bit larger than w_cc so this is a bit lazy
        self.dh = 4*self.Acs / (2*self.h_cc+2*self.w_cc)
        
    def r_liner_in(self,x):
        '''Returns the radius of the inner liner wall at the given location as 
        a np.ndarray'''
        
        if type(x) is not np.ndarray:
            x = np.array(x)
        
        r = np.full(np.shape(x),np.nan)
        
        # cylindrical section
        cyl = x <= self.L_cyl
        r[cyl] = self.r_c
        # converging chamber cone
        con = np.logical_and(self.L_cyl < x, x <= self.L_c-self.dx_cu)
        r[con] = self.r_c - np.tan(self.theta_con)*(x[con]-self.L_cyl)
        # upstream throat curve 
        tcu = np.logical_and(self.L_c-self.dx_cu < x, x <= self.L_c)
        r[tcu] = self.r_t + self.rcu-np.sqrt(self.rcu**2-(self.L_c-x[tcu])**2)
        # downstream throat curve
        tcd = np.logical_and(self.L_c < x, x <= self.L_c+self.dx_cd)
        r[tcd] = self.r_t + self.rcd - np.sqrt(
            self.rcd**2-(x[tcd]-self.L_c)**2)
        # nozzle bell
        nbl = np.logical_and(self.L_c+self.dx_cd < x, x <= self.L_c+self.L_n)
        r[nbl] = np.polyval(self.bell_coefs, x[nbl]-self.L_c-self.dx_cd)+\
            self.r_t+self.dr_cd
        return r
                    
        
    def r_liner_out(self,x):
        '''Returns the radius of the liner outer wall at the given location'''
        return self.r_liner_in(x)+self.t_liner
    
    def r_jacket_in(self,x):
        '''Returns the radius of the inner jacket wall at the given location'''
        return self.r_liner_out(x)+self.h_cc
    
    def r_jacket_out(self,x):
        '''Returns the radius of the outer jacket wall at the given location'''
        return self.r_jacket_in(x)+self.t_j
        
    def dtheta_chan(self,x):
        '''Returns the angular width of the channel at the given location'''
        return self.w_cc/self.r_liner_out(x)
        
    def dtheta_fin(self,x):
        '''Returns the angular width of the fin at the given location'''
        return (2*np.pi*self.r_liner_out(x)/self.n_fin-self.w_cc)/\
            self.r_liner_out(x)
            
    def w_chan(self,x):
        '''Returns the width of the channel at the given location'''
        return self.dtheta_chan(x)*self.r_liner_out(x)
    
    def h_fin(self,x):
        '''Returns the height of the fin at the given location'''
        return self.r_jacket_in(x) - self.r_liner_out(x)
            
    def station_from_x(self,x):
        '''Returns the closest coolant station to the given x'''
        return np.argmin(abs(self.xc-x))
        
    def get_hc_liner(self,x):
        '''Returns the htc between the coolant liquid and liner at the given 
        location.'''
        # select the nearest station
        nc = self.station_from_x(x)
        # use the general liquid htc for the coolant
        return self.common_hl(nc)
        
    def get_hc_jacket(self,x):
        '''Returns the htc between the coolant liquid and jacket at the given 
        location.'''
        nc = self.station_from_x(x)
        # using the same value as the htc to the liner to start
        return self.common_hl(nc)
    
    def get_hg(self,x):
        '''Returns the hot gas htc at the given location.'''
        return self.bartz_hg(x)
        
    def get_Tc(self,x):
        '''Returns the temeprature of the coolant liquid at the given location.
        '''
        nc = self.station_from_x(x)
        return self.Tc[nc]
    
    def get_Taw(self,x):
        '''Returns the adiabatic wall temperature of the hot gas at the 
        given location.'''
        # TODO
        # trolling with a constant until latter but should actually do 
        # isentropic expansion then the adiabatic recovery temperature or smth
        return self.T0g # K
    
    def init_cooling(self):
        '''Sets initial temepratures in the coolant liquid.'''
        # coolant temperatures
        self.Tc = np.full(self.Nc,self.T_init_f,dtype=np.float32)
        # nusseult number init
        self.Nu = np.full(self.Nc,np.nan)

        self.update_cooling_parameters()
            
    def update_cooling(self):
        '''Updates the coolant temepratures based on the current wall 
        temepratures.'''
                
        # iterate through the cooling stations
        # the nc index of the coolant properties increases in the direction of 
        # coolant flow (default against the gas flow)
        for nc in range(self.Nc):
            # don't calculate the temperature of the inlet station because 
            # it is assumed to always be the inlet temperature 
            if nc == 0:
                continue
            # start and end x values of this station
            # remember that x decreases and n increases
            x0,x1 = self.xc[nc-1:nc+1]
            
            # notes on this calculation: 
            # the actual model splits the fin and channel in half, however
            # this calculation uses the entire channel surface area to get the 
            # total heat flow. this works because the fem returns the flux
            # this also corresponds to using mdot/Nc as the flow rate in each 
            # single channel
            
            # TODO: unfuck this
            # x distance between stations
            dx = abs(x1-x0)
            # average x location
            x_avg = (x1-x0)/2
            # width of the channel
            w = self.w_chan(x_avg)
            # height of the finn
            h = self.h_fin(x_avg)
            # heat flux from the liner cold wall
            q_lwc = self.model.get_heat_flux('liner_in_chan','r+',x0,x1)
            # heat flux from the fin inner wall
            q_fin = self.model.get_heat_flux('fin','theta-',x0,x1)
            # specific heat capacity
            cp0 = self.fuel_props.get('cp',T=self.Tc[nc-1])
            cp1 = self.fuel_props.get('cp',T=self.Tc[nc])
            cp= (cp0+cp1)/2
            
            # heat flow into fuel between these stations
            Q = (w*q_lwc+2*h*q_fin)*dx
            
            # calculate the next temperature            
            self.Tc[nc] = self.Tc[nc-1] + Q/(self.mdot_f/self.Nc*cp)
            
        # call this so that when the bcs are reapplied they will have the most
        # recent Re and Pr for the htc
        self.update_cooling_parameters()
            

    def update_cooling_parameters(self):
        '''Updates the nondimensional guys in the regen based on the current 
        temperatures'''
        
        # density
        self.rho = np.array([self.fuel_props.get('rho',T=self.Tc[nc]) 
                             for nc in range(self.Nc)])
        # conductivity
        self.k = np.array([self.fuel_props.get('k',T=self.Tc[nc])
                          for nc in range(self.Nc)])
        
        # specific heat capacity
        self.cp = np.array([self.fuel_props.get('cp',T=self.Tc[nc])
                            for nc in range(self.Nc)])
        
        # viscosity
        self.mu = np.array([self.fuel_props.get('mu',T=self.Tc[nc])
                            for nc in range(self.Nc)])

        # velocity
        self.v = self.mdot_f/(self.Acs*self.rho)
        
        # reynolds number
        self.Re = self.rho*self.v*self.dh/self.mu
        
        # prandtl number
        self.Pr = self.cp*self.mu/(self.k)      
        
            
    
    def get_max_Tc(self):
        '''Returns the coolant temperature at the end of the passsage.'''
        return max(self.Tc)
    
    def common_hl(self,nc):
        '''Returns the coolant htc assuming the same equation is used for the
        inner and outer surfaces'''
        return self.colburn_hl(nc)
    
    def colburn_hl(self,nc):
        '''Returns the coolant htc using the colburn equation (AHTT 7.39a)'''
        self.Nu[nc] = 0.023 * self.Re[nc]**0.8 * self.Pr[nc]**(1/3)
        return self.Nu[nc]*self.fuel_props.get('k',T=self.Tc[nc])/self.dh[nc]
    
    def bartz_hg(self,x):
        '''Returns the hot gas htc using the bartz equation (HH-4-13)'''
        # TODO this kinda sucks to implement so imma just troll with this for 
        # now until everything else is working
        return 1000 # W/m^2-K
    
    def export_results(self,output_fname=None):
        if output_fname is None:
            output_fname = 'results_'+self.input_fname
        print('writing results to ',output_fname,'...')
                
        # now the coolant properties at each station
        # want n	x	T	rho	cp	mu	k	v	dh	Re	Pr	Nu	hl
        hl = [self.get_hc_liner(self.xc[nc]) for nc in range(self.Nc)]
        
        regen_tbl = pd.DataFrame({'station':list(range(self.Nc)),
                     'x':self.xc,
                     'T':self.Tc,
                     'rho':self.rho,
                     'cp':self.cp,
                     'mu':self.mu,
                     'k':self.k,
                     'v':self.v,
                     'dh':self.dh,
                     'Re':self.Re,
                     'Pr':self.Pr,
                     'Nu':self.Nu,
                     'hl':hl})
        with pd.ExcelWriter(output_fname) as writer:
            regen_tbl.to_excel(writer,sheet_name='regen')
        
        # data from the solid walls
        # hot wall
        # need to get all the sol_ids
        # the hot wall is the r- faces of the liner_in_chan and liner_on_fin
        hw_nodes = np.concatenate([self.model.bodies[body].faces['r-']
                                for body in ['liner_in_chan','liner_on_fin']])
        
        # cold wall nodes
        # this is just the base of the channel, not the side of the fins
        cw_nodes = self.model.bodies['liner_in_chan'].faces['r+']
        
        # center fin nodes
        # since the fin is split by symmetry, this is just the theta+ face
        fn_nodes = self.model.bodies['fin'].faces['theta+']

        # going to use a helper function to take the nodes and plot their 
        # temperatures
        self.export_surf_Ts(hw_nodes,'hot wall',output_fname,'hot_wall')
        self.export_surf_Ts(cw_nodes,'cold wall',output_fname,'cold_wall')
        self.export_surf_Ts(fn_nodes,'center of fin',output_fname,'fin_center')

        # and the gas properties at each station
        # station	x	Taw	hg
        gas_tbl = pd.DataFrame({'station':list(range(self.Nc)),
                                'x':self.xc,
                                'Taw':[self.get_Taw(x) for x in self.xc],
                                'hg':[self.get_hg(x) for x in self.xc]})
        with pd.ExcelWriter(output_fname,mode='a') as writer:
            gas_tbl.to_excel(writer,sheet_name='gas')
        
        # let's throw in the node table and full temperature list too
        with pd.ExcelWriter(output_fname,mode='a') as writer:
            self.model.node_tbl.to_excel(writer,sheet_name='node_tbl')
            self.model.T.to_excel(writer,sheet_name='all_Ts')
            
        print('done!')
        
    def export_surf_Ts(self,nodes,label,fname,sheet):
        '''Helper to write the n, x, theta, r, T of the nodes to the result sheet.'''
        # TODO: write the label above the data
        coords = self.model.node_tbl.loc[nodes,['x','theta','r']]
        sol_ids = self.model.node_tbl.loc[nodes,'sol_id']
        Ts = self.model.T.loc[sol_ids]
        
        tbl = pd.DataFrame({'node':nodes, 'x':coords.x.values,
                            'theta':coords.theta.values, 'r':coords.r.values,
                           'T':Ts.values})
        with pd.ExcelWriter(fname,mode='a') as writer:
            tbl.to_excel(writer,sheet_name=sheet)
        
        
class Fluid:
    '''Represents a fluid with temperature dependent properties.
    
    Available properties: k [W/(m*K)], cp [J/(kg*K)], rho [kg/m^3], mu [Pa-s]
    
    Uses default data sheet at ./input_sheets/fluids.xlsx
    '''
    
    def __init__(self,name):
        ''' 
        Inputs:
            name - the species of fluid
        '''
        fname = 'input_sheets/fluids.xlsx'
        self.data = pd.read_excel(fname,sheet_name=name)
        
    def get(self,prop,T=None):
        '''Returns the value of prop at temperature T [K].'''
        if T is None:
            return self.data.loc[0,prop]
        else:
            return np.interp(T,self.data['T'],self.data[prop])
            
            
        
        
    
    

