
def simulate_bug():
    # 1. Setup simulated DB data (lowercase tags as per logic/mission_pars.py)
    # squad_map keys are t.lower()
    squad_map = {
        "alpha": "Alpha Squad",
        "75th": "75th Ranger"
    }

    # 2. Simulate extraction (returns uppercase as per logic/name_logic.py)
    extracted_squad_text = "ALPHA"
    extracted_squad_numeric = "75TH"

    print(f"Testing text squad: '{extracted_squad_text}'")
    
    # CURRENT BUGGY LOGIC
    if extracted_squad_text in squad_map:
        print("MATCH FOUND (Unexpected for bug)")
    else:
        print("MATCH FAILED (Reproduced bug)")

    print(f"Testing numeric squad: '{extracted_squad_numeric}'")
    # CURRENT BUGGY LOGIC
    # Wait, '75TH' is uppercase. '75th' is lowercase. They are NOT equal.
    # User said numeric works. '75' and '75' are equal. '75th' and '75TH' are NOT.
    # If the user has "75" as a tag, then upper() is "75", lower() is "75".
    
    extracted_squad_pure_numeric = "75"
    squad_map_numeric = {"75": "75th Ranger"}
    
    if extracted_squad_pure_numeric in squad_map_numeric:
        print("MATCH FOUND for pure numeric (Expected)")
    else:
        print("MATCH FAILED for pure numeric")

    # 3. Verify Fix
    print("\n--- Verifying Fix ---")
    if extracted_squad_text.lower() in squad_map:
        print(f"FIXED: '{extracted_squad_text}' matched to '{squad_map[extracted_squad_text.lower()]}'")
    else:
        print("FIX FAILED")

if __name__ == "__main__":
    simulate_bug()
