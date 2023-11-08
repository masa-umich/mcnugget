
clear; clc

h = 4500; % W/m^2-K
k = 345; % W/m-K
t = unit_convert(0.040:0.001:0.080,'in','m'); % m
l = unit_convert(0.040:0.001:0.080,'in','m'); % m

[T,L] = meshgrid(t,l);

m = @(t) sqrt(2*h./(k*t));

etaf = @(t,l) tanh(m(t).*l)./(m(t).*l);

Etaf = etaf(T,L);

figure
surf(unit_convert(T,'m','in'),unit_convert(L,'m','in'),Etaf)
xlabel('thickness [in]'); ylabel('length [in]')
title('Fin Efficiency')

figure


