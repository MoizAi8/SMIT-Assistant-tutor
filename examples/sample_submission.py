# Temperature Converter
# A program to convert between Celsius and Fahrenheit

def celsius_to_fahrenheit(celsius):
    result = (celsius * 9/5) + 32
    return result

def fahrenheit_to_celsius(fahrenheit):
    result = (fahrenheit - 32) * 5/9
    return result

def main():
    print("Temperature Converter")
    temp = input("Enter temperature: ")
    scale = input("Is this Celsius or Fahrenheit? (C/F): ")
    
    if scale.upper() == "C":
        converted = celsius_to_fahrenheit(float(temp))
        print(f"{temp}°C = {converted}°F")
    elif scale.upper() == "F":
        converted = fahrenheit_to_celsius(float(temp))
        print(f"{temp}°F = {converted}°C")
    else:
        print("Please enter C or F")

main()
