classdef Fluid
    % Fluid has fluid properties
    %   viscosity, specific heat, conductivity, density
    
    properties
        data
    end
    
    methods
        function obj = Fluid(infilename)
            %Fluid Construct an instance of this class
            %   give filename to csv of T,cp,rho,mu,k
            obj.data = readmatrix(infilename);
        end
        
        function value = cp(obj,T)
            value = interp1(obj.data(:,1), obj.data(:,2), T,'linear','extrap');
        end
        function value = rho(obj,T)
            value = interp1(obj.data(:,1), obj.data(:,3), T,'linear','extrap');
        end
        function value = mu(obj,T)
            value = interp1(obj.data(:,1), obj.data(:,4), T,'linear','extrap');
        end
        function value = k(obj,T)
            value = interp1(obj.data(:,1), obj.data(:,5), T,'linear','extrap');
        end
    end
end

