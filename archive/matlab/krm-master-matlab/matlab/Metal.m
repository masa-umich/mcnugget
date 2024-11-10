classdef Metal
    % Metal has metal properties
    %   yield strength, ultimate strength
    
    properties
        data
    end
    
    methods
        function obj = Metal(infilename)
            % Metal Construct an instance of this class
            %   give filename to csv of T,sty,stu
            obj.data = readmatrix(infilename);
        end
        
        function value = sty(obj,T)
            value = interp1(obj.data(:,1), obj.data(:,2), T,'linear','extrap');
        end
        function value = stu(obj,T)
            value = interp1(obj.data(:,1), obj.data(:,3), T,'linear','extrap');
        end

    end
end

