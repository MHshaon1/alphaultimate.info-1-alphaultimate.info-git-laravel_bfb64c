// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AlphaBuildLog {
    struct LogEntry {
        string category; // e.g. "delay", "material", "cash"
        string message;
        string date;
        address author;
    }

    LogEntry[] public logs;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function addLog(string memory category, string memory message, string memory date) public {
        logs.push(LogEntry(category, message, date, msg.sender));
    }

    function getLog(uint index) public view returns (string memory, string memory, string memory, address) {
        require(index < logs.length, "Invalid index");
        LogEntry storage entry = logs[index];
        return (entry.category, entry.message, entry.date, entry.author);
    }

    function getLogCount() public view returns (uint) {
        return logs.length;
    }
}