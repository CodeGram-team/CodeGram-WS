def extract_java_main_class(code:str) -> str | None:
    """
    Extract public class name include 'public static void main' in Java code
    """
    if "public static void main" not in code:
        return None
    
    for line in code.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("public class"):
            parts = stripped_line.split()
            if len(parts) >= 2: # "public", "class", "Name"
                class_name = parts[2] if len(parts) > 2 else ""
                if '{' in class_name:
                    class_name = class_name.split('{')[0]
                return class_name.strip()