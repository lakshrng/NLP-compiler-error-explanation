class Shape {
    virtual void draw() = 0;
};

int main() {
    Shape s; // cannot declare variable ‘s’ to be of abstract type ‘Shape’
    return 0;
}
