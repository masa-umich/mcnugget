function output = unit_convert(input, input_unit, output_unit)
    output = input * double(unitConversionFactor(input_unit,output_unit));
end
