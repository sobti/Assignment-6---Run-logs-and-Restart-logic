#include <iostream>
#include <unordered_map>
#include <algorithm>
#include <numeric>
#include "IntcodeComputer.h"
#include "Screen.h"
#include "vector"
#include <unordered_map>
#include <iterator>
#include <sstream>
#include <zconf.h>

using namespace std;

struct Pos {
    int x;
    int y;
    Pos move(int direction) const {
        Pos result {x, y};
        switch (direction) {
            case 0:
                result.y -=1;
                break;
            case 1:
                result.x +=1;
                break;
            case 2:
                result.y +=1;
                break;
            case 3:
                result.x -=1;
                break;
        }
        return result;
    }

    bool operator==(const Pos &other) const{
        return x == other.x && y == other.y;
    }

    bool operator!=(const Pos &other) const{
        return x != other.x || y != other.y;
    }
};

// Required by unordered_map
template<> struct std::hash<Pos> {
    std::size_t operator() (const Pos &node) const {
        return (hash<int>()(node.x) << 4) ^ hash<int>()(node.y);
    }
};


struct State {
    string path;
    vector<string> program;
    vector<string> commands;
    bool is_valid;
};

int command_length(string command);
std::string steps_to_str(int steps);
State solve(State state);



string inputs = "";
int inp_pos = 0;
long on_input() {
    long result = inputs[inp_pos++];
    return result;
}

IntcodeComputer computer;

int main() {
    Screen screen;
    computer.load_program("program.txt");

    std::unordered_map<Pos, int> map;

    int x=1;
    int y=1;
    Pos robot;
    screen.cls();
    while (!computer.is_halted()) {
        while (!computer.step(false, on_input)) {
            ;
        }
        char ch = computer.get_last_output();
        Pos pos {x, y};
        if (ch == '#') {
            map[pos] = 1;
        }
        if (ch == '^') {
            robot = pos;
        }
        if (ch != 10) {
            screen.text(x, y, std::string(1,ch));
        }
        if (ch == 10) {
            y++;
            x=1;
        }
        else {
            x++;
        }
    }
    int rows = y+1;
    int cols = x+1;

    int sum = 0;


    for (const auto &pair: map) {
        auto &pos = pair.first;
        if (pos.x == 0 || pos.y == 0 || pos.x == cols-1 || pos.y == rows -1) {
            continue;
        }
        bool is_intersection = true;
        for (int dir = 0; dir < 4; dir++) {
            auto neighbour = pos.move(dir);
            if (!map.count(neighbour)) {
                is_intersection = false;
                break;
            }
        }
        if (is_intersection) {
            sum+= pos.x * pos.y;
        }
    }

    screen.text(1,40, " ");
    std::cout << std::endl << "Sum of the alignment parameters: " << sum << std::endl;


    std::string path;
    int dir = 0;
    Pos robot_pos = robot;
    do {
        int steps = 0;
        auto forward = robot_pos.move(dir);

        while (map.count(forward)) {
            robot_pos = forward;
            steps++;
            forward = robot_pos.move(dir);
        }
        if (steps) {
            path += steps_to_str(steps);
        }

        auto left = robot_pos.move((dir+3) % 4);
        if (map.count(left)) {
            path+="L";
            dir = (dir+3) % 4;
            continue;
        }
        auto right = robot_pos.move((dir+1) % 4);
        if (map.count(right)) {
            path+="R";
            dir = (dir+1) % 4;
            continue;
        }
        break;
    } while(true);

    std::cout << "Path: " << path << std::endl;

    State state;
    state.path = path;
    state.is_valid = false;
    state.program.clear();
    state.commands.clear();

    State solution = solve(state);
    if (!solution.is_valid) {
        cout << "Solition not found!" << endl;
        return -1;
    }




    string program =  std::accumulate(
        solution.program.begin(),
        solution.program.end(),
        string(),
        [](string &acc, string &code) {
            return acc.empty() ? code : acc + "," + code;
        });
    inputs += program + '\x0A';


    for (const string &command : solution.commands) {
        string command_str =  std::accumulate(
                command.begin(),
                command.end(),
                string(),
                [](string &acc, const char &code) {
                    string st;
                    if (code == 's') {
                        st = "6";
                    } else if (code == 'e') {
                        st = "8";
                    } else if (code == 't') {
                        st = "12";
                    } else {
                        st = code;
                    }
                    return acc.empty() ? st : acc + "," + st;
                });
        inputs += command_str + '\x0A';
    }

    computer.load_program("program.txt");
//    computer.reset();
    computer.ram[0] = 2;    // wake the vacuum robot

    inputs += "n"; // np video

    while (!computer.is_halted()) {

        bool out = computer.step(false, on_input);
        if (out) {
            auto last = computer.get_last_output();
            if (last > 256) {
                cout << "Vacuum robot report: " << last << endl;
                break;
            }
        }
    }

    return 0;

}

State solve(State state) {


    // Try re-use existing commands
    if (state.program.size() < 20 && !state.commands.empty()) {
        for (int i = 0; i < state.commands.size(); i++) {
            string command = state.commands[i];
            if (command == state.path) {
                state.program.push_back( string(1, 'A' + i));
                state.is_valid = true;
                return  state;
            }
            if (state.path.rfind(command, 0) == 0) { // remaining path starts with a command

                State newState {
                        state.path.substr(command.length(), 1000),
                        state.program,
                        state.commands,
                        false,
                };
                newState.program.push_back( string(1, 'A' + i));
                State res = solve(newState);
                if (res.is_valid) {
                    return res;
                }
            }
        }
    }

    // Try add new command
    if (state.commands.size() < 3) {
        for (int com_length = 2; com_length <= state.path.size(); com_length+=2) {
            auto candidate = state.path.substr(0, com_length);

            if (find(state.commands.begin(), state.commands.end(), candidate) != state.commands.end()) {
                //command already in the list, skip it
                continue;
            }
            if (command_length(candidate) <= 20) {
                State newState {
                        state.path,
                        state.program,
                        state.commands,
                        false,
                };
                newState.commands.push_back(candidate);
                State res = solve(newState);
                if (res.is_valid) {
                    return res;
                }
            }
            else {
                break;
            }
        }
    }
    state.is_valid = false;
    return state;
}

std::string steps_to_str(int steps) {
    switch (steps) {
        case 6:
            return "s";
        case 8:
            return "e";
        case 12:
            return "t";
        default:
            return "?";
    }
}

int command_length(string command) {
    int result = 0;
    for (const auto &ch: command) {
        if (ch == 't') {
            result +=3;
        }
        else {
            result+=2;
        }
    }
    return result - 1; // do not include last comma
}