
clear; clc; close all

R = unit_convert(6/2,'in','m');
Tb = 600; % K
Tinf = 300; % K
h = 4500; % W/m^2-K
k = 345; % W/m-K
A = 2.9961e-04; % m^2 (from marpa_copper_rpd2.m)
w = 1; % cancels out

% defining the height of the channel by the total flow area
L = @(N,t) A./(2*pi*R-N.*t);

% hl is heat flow rate divided by temperature difference and total base
% area (without channels)
% hL(N,t) = @(N,t) 1/(2*pi*R)*h*(2*pi*R+(2*L(N,t)-t).*N).*...
%     (1-(2*N*L(N,t))./(2*pi*R+(2*L(N,t)-t).*N) .* ...
%     (1-tanh(sqrt(2*h./(k*t)).*L(N,t))./(sqrt(2*h./(k*t))*L(N,t))));

m = @(N,t) sqrt(2*h./(k*t));

etaf = @(N,t) tanh(m(N,t).*L(N,t))./(m(N,t).*L(N,t));

Af = @(N,t) 2*L(N,t)*w;

At = @(N,t) w*(2*pi*R - N.*t + 2*N.*L(N,t));

etao = @(N,t) 1-N.*Af(N,t)./At(N,t).*(1-etaf(N,t));

q = @(N,t) h * At(N,t) .* etao(N,t) * (Tb-Tinf);

hl = @(N,t) q(N,t)./(w*(Tb-Tinf)*(2*pi*R));

t_range = 0.02:0.001:0.08; % in

Nt = 2*pi*R - A/L(96,unit_convert(0.04,'in','m'));

t = unit_convert(t_range,'in','m');

N = Nt./t;

figure
plot(N, hl(N,t)/h)
xlabel('Number of Channels'); ylabel('Heat Flux Increase')

figure
plot(N, etaf(N,t))
xlabel('Number of Channels'); ylabel('Fin Efficiency')

figure
plot(N, L(N,t))
xlabel('Number of Channels'); ylabel('Fin Length')






