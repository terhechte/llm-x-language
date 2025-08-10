
public class Person
{
    public string Name { get; set; }
    public int Age { get; set; }
    
    public override string ToString()
    {
        return $"{Name} is {Age} years old";
    }
}

var person = new Person { Name = "Alice", Age = 30 };
Console.WriteLine(person);
