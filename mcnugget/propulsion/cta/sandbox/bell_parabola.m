
clear; clc; format compact

% x2 = 102.4 - 2.19
% y2 = 46.7-12.99
% theta_i = deg2rad(27.4)

% x2 = 83.6 - 1.16
% y2 = 35.5 - 5.94
% theta_i = deg2rad(33)

% x2 = 68.1 - 1.13
% y2 = 31.25 - 5.64
% theta_i = deg2rad(34)

x2 = 65.36 - (75.89/2)*0.38*sind(24.69)
y2 = (129.10-75.89)/2 - (75.89/2)*0.38*(1-cosd(24.69))
theta_i = deg2rad(24.69)

theta = theta_i - 1/2*pi

u2 =  cos(theta)*x2 + sin(theta)*y2
v2 = -sin(theta)*x2 + cos(theta)*y2

a = u2/v2^2

du_dv2 = 2*a*v2

theta_ep = pi/2 - atan(du_dv2)

theta_e = theta_ep + theta;
rad2deg(theta_e)

% theta_e = deg2rad(9.8);
% 
% A = [y2^2 y2; 2*y2 1]
% B = [x2; tan(pi/2-theta_e)]
% 
% x = A\B
% 
% a = x(1); b = x(2)
% 
% dx_dy1 = b
% theta_i = pi/2 - atan(dx_dy1)
% rad2deg(theta_i)
% 
% a*y2^2+b*y2
% 2*a*y2+b

