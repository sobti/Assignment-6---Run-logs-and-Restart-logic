package javaTest;

public class RunPoint {

    public static void main(String[] args) {

        Point p1 = new Point(1, 0);

        System.out.println("Координты точки p1.x = " + p1.x + ", p1.y =" + p1.y);


        Point p2 = new Point(3, 0);


        System.out.println("Координты точки p2.x = " + p2.x + ", p2.y = " + p2.y);

        System.out.println("Расстояние между p1 и p2 = " + p1.distance(p2));

    }
}
