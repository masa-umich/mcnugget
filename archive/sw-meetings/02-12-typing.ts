
// Type System
// 
// TypeScript and JavaScript - Dynamically Typed and a Statically Typed
// JavaScript and TypeScript - Elixir and Elm
//
// What are dynamically typed languages good for?
// 
// Writing programs quickly and without needing have CS knowledge.
// Complex Software Engineering - Downside of dynamic typing.
//
// TypeScript is an emergent solution to this problem. TypeScript is a statically typed
// version of JavaScript.
//
// TypeScript is really type hinted, there's no compile time checking.
// Same case with type hinting in Python.
//
// C++, Go, Java, C# - Statically Typed
//
// TypeScript 'compiles' to JavaScript, which is really just a runtime on top of C++.
// Browser is a type of runtime (or 'interpereter') for JavaScript (HTML, CSS). 
// Same with Python.
// Executing your code 'one step' at a time.


// Union Types
type WiderNumber = number | BigInt


function add<T>(a: T, b: T): T {

}

interface Barker {
    bark: () => void
}

const barkTwice = <B extends Barker>(dog: B): B => {
    dog.bark()
    dog.bark()
    return dog
}

class Dog implements Barker {
    age: number = 10
    bark() {
        console.log('woof')
    }
}

const dog = new Dog()
const dogTwo = barkTwice(dog)
console.log(dogTwo.age)

