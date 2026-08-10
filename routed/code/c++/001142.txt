#include <iostream>
#include <cmath>
#include <algorithm>
#include <vector>
using namespace std;
int main() {
    string s, t, u; cin >> s >> t >> u;
    if (s.length() == 5 && t.length() == 7 && u.length() == 5) cout << "valid" << endl;
    else cout << "invalid" << endl;
}
