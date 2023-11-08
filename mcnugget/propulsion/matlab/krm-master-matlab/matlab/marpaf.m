function [results] = marpaf(rc_w)
%% Citrus Chamber Code

% KEY INPUT
% absolute roughness
rc.e = 0.05e-3; % m
% fuel channel width
rc.w = rc_w;
% percent soot resistance
soot_percent = 1;

% LINER MATERIAL PROPERTIES
% % modulus
% c.E = 200e9; % Pa
% % coefficient of thermal expansion
% c.a = 11e-6;
% % poisson ratio
% c.v = 0.275;
% % chamber wall thermal conductivity
% c.k = 26.5; % W/m-K
% % metal liner properties
% metal = Metal('410_properties.csv');

% modulus
c.E = 120e9; % Pa
% coefficient of thermal expansion
c.a = (10.2*1.8)*1e-6;
% poisson ratio
c.v = 0.34;
% chamber wall thermal conductivity
c.k = 345; % W/m-K
% metal liner properties
metal = Metal('18150_properties.csv');

% liner inner diameter
c.di = convlength(5.875, 'in', 'm');
% jacket inner diameter
c.jid = convlength(6.095, 'in', 'm'); % m

% % thermal expansion temperature
% steel
% cte_ref = -70136273 * rc.w^2 + 488027 * rc.w + 395; % K
% copper
cte_ref = -95631530 * rc.w^2 + 571598 * rc.w + 324; % K


% thermal strain
e_th = (cte_ref - 300) * c.a;
% liner inner diameter expansion
d_th = e_th * c.di;

% chamber wall thickness
c.t = (c.jid - (c.di + d_th))/2 - rc.w;

% particular n
np = 30;

% INPUT
% gas convection coefficient from RPA
rpa = RPA('gas_convection.csv');

% fuel properties
fuel = Fluid('fluid_properties.csv');

% Engine
% fuel mass flow rate
mdot = 1.55; % kg/s
% regen inlet pressure
p_init = convpres(330,'psi','Pa'); % psi
% chamber pressure
c.pc = convpres(233.5,'psi','Pa'); % psi
% initial fuel temperature
Tc_init = 300; % K
% initial wall temperature
Twh_init = 300; % K
Twc_init = 300; % K
% adiabatic wall temperature
Taw = 3300; % K
% radiative heat flux
q_rad = 000e3; % W/m^2

% Geometry
% number of stations
N = 100;

% chamber length
c.L = convlength(9.9983, 'in', 'm');

% fuel channel length
rc.L = convlength(12.93, 'in', 'm');

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
x = linspace(-rc.L,0,N);
% n at nozzle inlet
ni = find(abs(x+c.L) == min(abs(x+c.L)));
np = ni;
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
% Reynolds number
Re = init;
% Prandtl number
Pr = init;
% Nusselt number
Nu = init;

% unheated region
Tc(1:ni) = Tc_init;
Twc(1:ni) = Twc_init;
Twh(1:ni) = Twh_init;

rho(1:ni) = fuel.rho(Tc(1:ni));
mu(1:ni) = fuel.mu(Tc(1:ni));
k(1:ni) = fuel.k(Tc(1:ni));
cp(1:ni) = fuel.cp(Tc(1:ni));
v(1:ni) = mdot ./ (rc.A * rho(1:ni));
Re(1:ni) = rho(1:ni) .* v(1:ni) * rc.dh ./ mu(1:ni);

Twh_eps = 0.1; % K
Twc_eps = 0.1; % W/m^2-K

% Simulation
for n = ni:N
    if true
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
        hge(n) = 1/(1/hg(n)+soot_percent/c.hs);
%         hge(n) = (hg(n)*c.hs)/(hg(n) + c.hs);
        % heat flux
        q(n) = (Taw-Tc(n))/(1/hg(n) + soot_percent/c.hs + c.t/c.k + 1/hl(n)) + q_rad;
        % hot wall temperature
        Twh_prev = Twh(n);
        Twh(n) = Taw - (q(n)-q_rad)/hge(n);
        % cold wall temperature
        Twc_prev = Twc(n);
        Twc(n) = Twh(n) - q(n)*c.t/c.k;
    end
    
%     fprintf('n: %3.f Twh: %.0f Twc: %.0f Tc: %.0f\n', n, Twh(n), Twc(n), Tc(n))

    % next coolant temperature
    if n~=N
        Tc(n+1) = Tc(n) + (q(n) * c.As)/(mdot * cp(n));
    end
    
end

% pressure drop

options = optimset('Display', 'off');

% Colbrook-White Equation
cw = @(f,Re,e,dh) 1/sqrt(f) + 2*log10(e/(3.7*dh) + 2.51/(Re*sqrt(f)));
% Darcy-Weisbach Equation
dw = @(L,f,rho,v,D) f.* L./D .* 1/2.*rho.*v.^2;

for n = 1:N
    rc.f(n) = fsolve(@(f) cw(f,Re(n),rc.e,rc.dh), 0.02, options);
end

dp = -dw(dx, rc.f, rho, v, rc.dh);

p = cumsum(dp);

% structural calculations

% inner wall thermal stress
sigma_th_di = c.E * c.a * (Twc-Twh) / (2 * (1-c.v));
% outer wall thermal stress
sigma_th_do = c.E * c.a * (Twh-Twc) / (2 * (1-c.v));
% pressure stress sigma = p r / t
sigma_p = (c.pc - (p_init + p)) * rc.di/2 / c.t;

sigma_di = sigma_p + sigma_th_di;

sigma_th_max = c.E * c.a * max(Twh-Twc) / (2 * (1-c.v));

% yield strength
sty = metal.sty(Twh);
% ultimate strength
stu = metal.stu(Twh);

% bending stress
sb = 0; % convpres(32e3,'psi','Pa');

% safety factor to yield
SFY = sty ./ (abs(sigma_di)+sb);
% safety factor to ultimate
SFU = stu ./ (abs(sigma_di)+sb);

% fprintf('\n')
% fprintf('Liner Wall Thickness: %.3f in\n', convlength(c.t, 'm', 'in'))
% fprintf('Liner Diameter Expansion: %.3f in\n', convlength(d_th, 'm', 'in'))
% fprintf('Total Pressure Drop: %.1f psi\n', convpres(p(end)-p(1), 'Pa', 'psi'))
% fprintf('Maximum Temperature Gradient: %.0f K\n', max(Twh-Twc))
% fprintf('Maximum Liner Thermal Stress: %.1f ksi\n', convpres(max(abs(sigma_th_di)),'Pa','psi')/1e3)
% fprintf('Maximum Liner Pressure Stress: %.1f ksi\n', convpres(max(abs(sigma_p)),'Pa','psi')/1e3)
% fprintf('Maximum Liner Combined Stress: %.1f ksi\n', convpres(min(sigma_di),'Pa','psi')/1e3)
% fprintf('Minimum Safety Factor Yield: %.1f\n', min(SFY))
% fprintf('Minimum Safety Factor Ultimate: %.1f\n', min(SFU))
% fprintf('Maximum Liner Temperature: %.0f K (%.0f F)\n', max(Twh), convtemp(max(Twh),'K','F'))
% fprintf('Gas Convective Coefficient at n = %.0f: %.0f W/m^2-K\n', np, hg(np))
% fprintf('Liquid Convective Coefficient at n = %.0f: %.0f W/m^2-K\n', np, hl(np))
% fprintf('Heat Flux at n = %.0f: %.1f MW/m^2\n', np, q(np)/1e6)

results.dp = p(end)-p(1);
results.maxTwh = max(Twh);
results.maxTwc = max(Twc);
results.maxdT = max(Twh-Twc);
results.maxTc = Tc(end);
results.stress = min(sigma_di);
results.ct = c.t;
results.SFY = min(SFY);
results.SFU = min(SFU);
results.cte_ref = cte_ref;
results.d_th = d_th;

end

