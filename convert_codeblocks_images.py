import base64
import os

def image_to_base64(filepath):
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/png;base64,{encoded_string}"

# Convert all images in frontend/public
public_dir = "frontend/public"
output_file = "codeblocks_images_base64.py"

with open(output_file, "w") as f:
    f.write("# Code::Blocks Images as Base64\n\n")
    
    for filename in os.listdir(public_dir):
        if filename.endswith(".png"):
            filepath = os.path.join(public_dir, filename)
            base64_string = image_to_base64(filepath)
            var_name = filename.replace(".", "_").replace("-", "_").replace("(", "").replace(")", "").replace(" ", "_")
            f.write(f"{var_name} = \"{base64_string}\"\n")
            print(f"Converted {filename}")

print(f"\nAll images converted and saved to {output_file}")
