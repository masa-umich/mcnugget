import pandas as pd
import os

def delete_data(file_list, start_index, end_index, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for file_path in file_list:
        try:
            # Read the CSV file
            data = pd.read_csv(file_path, header=None)

            # Filter data between start_index and end_index
            if start_index != -1 and end_index != -1:
                filtered_data = data.iloc[start_index:end_index + 1]
                # Save the filtered data to the new directory
                file_name = os.path.basename(file_path)
                output_file = os.path.join(output_dir, file_name)
                filtered_data.to_csv(output_file, index=False, header=False)
                print(f"Saved filtered data from {file_path} to {output_file}")
            else:
                print(f"Invalid indices for {file_path}, skipping.")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # file_list = ['data/65538.csv']  # Example list of files
    file_list = ['data/65538.csv', 'data/65602.csv', 'data/65616.csv', 'data/65762.csv', 'data/65574.csv', 'data/65560.csv', 'data/65548.csv', 'data/65549.csv', 'data/65561.csv', 'data/65575.csv', 'data/65763.csv', 'data/65617.csv', 'data/65603.csv', 'data/65615.csv', 'data/65601.csv', 'data/65761.csv', 'data/65749.csv', 'data/65563.csv', 'data/65577.csv', 'data/65588.csv', 'data/65589.csv', 'data/65576.csv', 'data/65562.csv', 'data/65748.csv', 'data/65760.csv', 'data/65600.csv', 'data/65614.csv', 'data/65610.csv', 'data/65604.csv', 'data/65758.csv', 'data/65566.csv', 'data/65572.csv', 'data/65599.csv', 'data/65598.csv', 'data/65573.csv', 'data/65567.csv', 'data/65759.csv', 'data/65605.csv', 'data/65611.csv', 'data/65607.csv', 'data/65613.csv', 'data/65559.csv', 'data/65571.csv', 'data/65565.csv', 'data/65564.csv', 'data/65570.csv', 'data/65558.csv', 'data/65612.csv', 'data/65606.csv', 'data/65675.csv', 'data/65715.csv', 'data/65701.csv', 'data/65700.csv', 'data/65714.csv', 'data/65674.csv', 'data/65676.csv', 'data/65689.csv', 'data/65702.csv', 'data/65716.csv', 'data/65717.csv', 'data/65703.csv', 'data/65688.csv', 'data/65677.csv', 'data/65673.csv', 'data/65698.csv', 'data/65707.csv', 'data/65713.csv', 'data/65712.csv', 'data/65706.csv', 'data/65699.csv', 'data/65672.csv', 'data/65670.csv', 'data/65710.csv', 'data/65704.csv', 'data/65705.csv', 'data/65711.csv', 'data/65671.csv', 'data/65683.csv', 'data/65697.csv', 'data/65720.csv', 'data/65708.csv', 'data/65709.csv', 'data/65721.csv', 'data/65696.csv', 'data/65682.csv', 'data/65669.csv', 'data/65694.csv', 'data/65680.csv', 'data/65681.csv', 'data/65695.csv', 'data/65691.csv', 'data/65685.csv', 'data/65733.csv', 'data/65684.csv', 'data/65690.csv', 'data/65679.csv', 'data/65686.csv', 'data/65692.csv', 'data/65693.csv', 'data/65687.csv', 'data/65678.csv', 'data/65757.csv', 'data/65555.csv', 'data/65541.csv', 'data/65569.csv', 'data/65596.csv', 'data/65582.csv', 'data/65583.csv', 'data/65597.csv', 'data/65568.csv', 'data/65540.csv', 'data/65554.csv', 'data/65756.csv', 'data/65620.csv', 'data/65608.csv', 'data/65754.csv', 'data/65542.csv', 'data/65556.csv', 'data/65581.csv', 'data/65595.csv', 'data/65594.csv', 'data/65580.csv', 'data/65557.csv', 'data/65543.csv', 'data/65609.csv', 'data/65619.csv', 'data/65751.csv', 'data/65547.csv', 'data/65553.csv', 'data/65584.csv', 'data/65590.csv', 'data/65591.csv', 'data/65585.csv', 'data/65552.csv', 'data/65546.csv', 'data/65750.csv', 'data/65618.csv', 'data/65752.csv', 'data/65578.csv', 'data/65550.csv', 'data/65544.csv', 'data/65593.csv', 'data/65587.csv', 'data/65586.csv', 'data/65592.csv', 'data/65545.csv', 'data/65551.csv', 'data/65579.csv', 'data/65753.csv']
    start = 85632  # Example start index
    end = 85779  # Example end index
    delete_data(file_list, start, end, 'xxx')
