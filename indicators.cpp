// Optional standalone C++ demonstration: compute simple moving average.
// Compile: g++ -O2 -std=c++17 cpp/indicators.cpp -o indicators
#include <iostream>
#include <vector>
#include <deque>
#include <iomanip>
int main() {
    std::size_t window;
    if (!(std::cin >> window) || window == 0) return 1;
    std::deque<double> values;
    double sum = 0, price;
    while (std::cin >> price) {
        values.push_back(price); sum += price;
        if (values.size() > window) { sum -= values.front(); values.pop_front(); }
        if (values.size() == window) std::cout << std::setprecision(12) << sum / window << '\n';
        else std::cout << "nan\n";
    }
}
