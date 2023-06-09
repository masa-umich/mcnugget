%% Citrus Chamber Code
clear; clc; close all

% INPUT
% gas convection coefficient from RPA
rpa = RPA('gas_convection.csv');

% fuel properties
fuel = Fluid('fluid_properties.csv');

% Engine
mdot = 1.55; % kg/s
% initial fuel temperature
Tc_init = 300; % K
% initial wall temperature
Twh_init = 600; % K
Twc_init = 500; % K
% adiabatic wall temperature
Taw = 3363; % K
% radiative heat flux
q_rad = 200e3; % W/m^2

% Geometry
% number of stations
N = 100;
c.di = convlength(6.1, 'in', 'm');
% chamber wall thickness
c.t = convlength(1/16, 'in', 'm');
% chamber length
c.L = 0.288; % m
% unheated portion of chamber
c.Ln = 0.288-0.250; % m
% fuel channel width
rc.w = convlength(0.025, 'in', 'm');
% absolute roughness
rc.e = 0.0032e-3; % m

% Material Properties
% chamber wall thermal conductivity
c.k = 27.4; % W/m-K
% soot heat transfer coefficient
c.hs = 1763; % W/m^2-K

% CALCULATIONS
% station dx
dx = c.L/N;
% chamber surface area per station
c.As = c.di*pi*dx;

% fuel channel inner diameter
rc.di = c.di + 2*c.t;
% fuel channel outer diameter
rc.do = rc.di + 2*rc.w;
% fuel channel area
rc.A = pi * (rc.do^2-rc.di^2)/4;
% perimeter
rc.P = pi * (rc.di + rc.do);
% hydraulic diameter
rc.dh = 4*rc.A/rc.P;
% relative roughness
rc.k = rc.e/rc.dh;

% INITIALIZATION
init = zeros(1,N);
% location
x = linspace(0,c.L,N);
% friction factor
rc.f = init;
% fuel temperature
Tc = init;
% cold wall temperature
Twc = init;
% hot wall temperature 
Twh = init;
% liquid convection coefficient
hl = init;
% gas convection coefficient
hg = init;
% effective gas convection coefficient
hge = init;
% heat flux
q = init;
% where heat flux is applied
qmap = ones(size(init));
qmap(x<c.Ln) = 0;
% fuel density
rho = init; % kg/m^3
% viscosity
mu = init; % Pa-s
% specific heat capacity
cp = init; % Pa-s
% fuel conductivity
k = init; % W/m-K
% fuel velocity
v = init; % m/s
% pressure
p = init; % Pa
% Reynolds number
Re = init;
% Prandtl number
Pr = init;
% Nusselt number
Nu = init;

% axial heat flux
qa = zeros(size(N,2));

% First station
Tc(1) = Tc_init;
Twc(1) = Twc_init;
Twh(1) = Twh_init;

Twh_eps = 0.1; % K
Twc_eps = 0.1; % W/m^2-K

% Simulation
for n = 1:N
    if n~=1
        Twh(n) = Twh(n-1);
        Twc(n) = Twc(n-1);
    end
    % density
    rho(n) = fuel.rho(Tc(n));
    % viscosity
    mu(n) = fuel.mu(Tc(n));
    % conductivity
    k(n) = fuel.k(Tc(n));
    % specific heat capacity
    cp(n) = fuel.cp(Tc(n));    
    % velocity
    v(n) = mdot / (rc.A * rho(n));
    % Reynolds number
    Re(n) = rho(n) * v(n) * rc.dh / mu(n);
    % Prandtl number
    Pr(n) = cp(n) * mu(n) / k(n);    
    
    Twc_prev = 0; Twh_prev = 0;
    while abs(Twc(n)-Twc_prev) > Twc_eps && abs(Twh(n)-Twh_prev) > Twh_eps
        % Nusselt number
        Nu(n) = 0.021 * Re(n)^0.8 * Pr(n)^0.4 * (0.64 + 0.36*Tc(n)/Twc(n));
        % liquid convective coefficient
        hl(n) = Nu(n) * k(n) / rc.dh;
                % gas convective coefficient
        hg(n) = rpa.hg(Twh(n));
        % effective gas convective coefficient
        hge(n) = (hg(n)*c.hs)/(hg(n) + c.hs);
        % heat flux
        q(n) = (Taw-Tc(n))/(1/hg(n) + 1/c.hs + c.t/c.k + 1/hl(n)) + q_rad;
        % hot wall temperature
        Twh_prev = Twh(n);
        
        Twh(n) = Taw - (q(n)-q_rad)/hge(n);
        % cold wall temperature
        Twc_prev = Twc(n);
        Twc(n) = Twh(n) - q(n)*c.t/c.k;
    end
    
    fprintf('n: %3.f Twh: %.0f Twc: %.0f Tc: %.0f\n', n, Twh(n), Twc(n), Tc(n))

    % next coolant temperature
    if n~=N
        Tc(n+1) = Tc(n) + (q(n) * c.As)/(mdot * cp(n));
    end
    
end













