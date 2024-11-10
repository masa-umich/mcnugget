
clear; clc; close all

R = unit_convert(6/2,'in','m');
Tb = 600; % K
Tinf = 300; % K
h = 4500; % W/m^2-K
k = 20; % W/m-K
A = 6 * unit_convert(5/32,'in','m') * 96 * unit_convert(0.030,'in','m');% 2.9961e-04; % m^2 (from marpa_copper_rpd2.m)
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

t_range = 0.04:0.01:0.08; % in

max_channels = 500;
min_base = unit_convert(0.04,'in','m');

Nmax = @(t) ceil(2*pi*R/(t+min_base));
Nmin = 1;

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, hl(N,t)/h,'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('Heat Flux Increase')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, etaf(N,t),'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('Fin Efficiency')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, etao(N,t),'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('Overall Surface Efficiency')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, L(N,t)/t,'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('L/t')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, Af(N,t),'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('Fin Area')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, L(N,t),'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('Fin Length')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(N, At(N,t),'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('Number of Channels'); ylabel('Total Area')
title('Regen Channel Optimization')
legend('location', 'best')

figure; hold on
for t = unit_convert(t_range,'in','m')
    N = Nmin:Nmax(t);
    plot(hl(N,t)/h, L(N,t)./t,'DisplayName',...
        sprintf('t=%.3f in',unit_convert(t,'m','in')))
end
xlabel('L/t Aspect Ratio'); ylabel('HTC Increase')
title('Regen Channel Optimization')
legend('location', 'best')
 





