# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 19:27:21 2024

@author: natecamp
"""

import cta_fem as cta

model = cta.Model('input_sheets/cta_fem_input_0.xlsx')

model.solve()

model.model.plot_mesh()

model.export_results('results/cta_fem_result_0.xlsx')
