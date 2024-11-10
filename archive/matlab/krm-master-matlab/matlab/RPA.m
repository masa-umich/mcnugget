classdef RPA
   
    properties
        data
    end
    
    methods
        function obj = RPA(infilename)
            obj.data = readmatrix(infilename);
        end
        
        function outputArg = hg(obj,T)
            %METHOD1 Summary of this method goes here
            %   Detailed explanation goes here
            outputArg = interp1(obj.data(:,1), obj.data(:,2), T, 'linear', 'extrap');
        end
    end
end

