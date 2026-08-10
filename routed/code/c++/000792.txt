#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <algorithm>

using std::begin;
using std::end;
using std::string;
using std::cin;
using std::cout;
using std::endl;
using std::get;
using std::vector;
using IntVec = std::vector<int>;

string STATE0{"#...##.#...#..#.#####.##.#..###.#.#.###....#...#...####.#....##..##..#..#..#..#.#..##.####.#.#.###"};

string RULES {R"(..... => .
..#.. => #
..##. => #
#..## => .
..#.# => #
####. => .
##.## => .
#.... => .
###.. => #
##### => #
##..# => #
#.### => #
#..#. => #
.#### => #
#.#.. => #
.###. => #
.##.. => #
.#... => #
.#.## => #
##... => #
..### => .
##.#. => .
...## => .
....# => .
###.# => .
#.##. => #
.##.# => .
.#..# => #
#.#.# => #
.#.#. => #
...#. => #
#...# => #)" };


auto value(const std::string& s)
{
    int v{0};
    for (auto ch : s)
    {
        v = v * 2 + (ch == '#');
    }
    return v;
};



auto task1(string state, string rules0)
{

    std::istringstream iss(rules0);
    string s, dummy, res;

    vector<int> rules(32, 0);

    while (iss >> s)
    {
        iss >> dummy;
        iss >> res;
        if (res[0] == '#')
        {
            rules[value(s)] = 1;
        }
           //cout << s << endl;
    }

    auto prev{STATE0 + "...."};
    //auto prev{STATE0};
    //prev += "....";
    auto pos{0};
    char token[2] = { '.', '#' };
    
    cout << endl;
    cout << prev << ":" << pos << ";" << prev.length() << endl;
    for (auto j = 1; j <= 20; ++j)
    {
        auto val{0u};
        string s;
        int plen {static_cast<int>(prev.length())};
        //s.reserve(prev.length() + 4);
        s.reserve(plen + 4);
       
        for (auto i = -4; i < plen - 4; ++i)
        {
            val = (val * 2 + (prev[i + 4] == '#')) & 31; 
            s += token[rules[val]];
        }
        s += "....";
        pos -= 2;
        cout << s << " , " << j << ", " << pos << endl;
        prev = s;
    }

    int result{0};
    for (auto ch : prev)
    {
        result += (ch == '#') * pos;
        ++pos;
    }

    return result;
}

int main()
{
    auto t = task1(STATE0, RULES);
    cout << t << endl;
    return 0;
}
