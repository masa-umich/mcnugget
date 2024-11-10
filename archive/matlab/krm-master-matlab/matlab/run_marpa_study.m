clear; close all; clc
tic
h_min = convlength(0.022, 'in', 'm');
h_max = convlength(0.065, 'in', 'm');
h_num = 87;
h_lst = linspace(h_min, h_max, h_num);

init = zeros(h_num,1);
dp = init;
maxTwh = init;
maxTwc = init;
maxdT = init;
maxTc = init;
stress = init;
ct = init;
SFY = init;
SFU = init;
cte_ref = init;
d_th = init;

for hi = 1:h_num
    results = marpaf(h_lst(hi));
    dp(hi) = results.dp;
    maxTwh(hi) = results.maxTwh;
    maxTwc(hi) = results.maxTwc;
    maxdT(hi) = results.maxdT;
    maxTc(hi) = results.maxTc;
    stress(hi) = results.stress;
    ct(hi) = results.ct;
    SFY(hi) = results.SFY;
    SFU(hi) = results.SFU;
    cte_ref(hi) = results.cte_ref;
    d_th(hi) = results.d_th;
end

max_avgTw = (maxTwc + maxTwh)/2;
toc

%%
close all

figure
plot(convlength(ct,'m','in'),convpres(stress/1e3,'Pa','psi'))
xlabel('Wall Thickness [in]'); ylabel('Stress [ksi]')
title('Maximum Combined Liner Stress')

figure
plot(convlength(ct,'m','in'),maxTwh)
xlabel('Wall Thickness [in]'); ylabel('Temperature [K]')
title('Maximum Hot Wall Temperature')

figure; hold on
plot(convlength(ct,'m','in'),SFY)
plot(convlength(ct,'m','in'),SFU)
xlabel('Wall Thickness [in]'); ylabel('Safety Factor')
title('Safety Factors')

figure
plot(convlength(ct,'m','in'),convlength(h_lst,'m','in'))
grid on
xlabel('Wall Thickness [in]'); ylabel('Regen Height [in]')
title('Regen Passage Height')

Twhpoly = polyfit(h_lst, max_avgTw,2);
Twhpoly_str = sprintf('y=%.3f x^2 + %.3f x + %.3f', ...
    Twhpoly(1),Twhpoly(2),Twhpoly(3));

figure; hold on
plot(convlength(h_lst,'m','in'), max_avgTw, 'o', 'HandleVisibility', 'off')
plot(convlength(h_lst,'m','in'), polyval(Twhpoly,h_lst), ...
    'DisplayName', Twhpoly_str)
xlabel('Regen Height [in]'); ylabel('Temperature [K]')
title('Maximum Average Wall Temperature')
legend('location', 'southwest')

figure
plot(max_avgTw, cte_ref)
grid on
xlabel('Maximum Average [K]'); ylabel('CTE Reference [K]')
title('Reference Temperatures')

figure
plot(convlength(ct,'m','in'), convpres(dp,'Pa','psi'))
xlabel('Wall Thickness [in]'); ylabel('Pressure Drop [psi]')
title('Regen Pressure Loss')

figure
plot(convlength(ct,'m','in'), convlength(d_th,'m','in'))
xlabel('Wall Thickness [in]'); ylabel('Diameter Expansion [in]')
title('Liner Thermal Expansion')
