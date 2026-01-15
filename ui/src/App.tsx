// import { useState } from "react";
import "./App.css";
import { ChatProvider } from "./ChatContext";
import { Chat } from "./components/chat";
import { Graph } from "./components/graph";

function App() {
  return (
    <div className="flex flex-col h-full">
      <ChatProvider>
        <Graph />
        <Chat className="z-1 w-lg" />
      </ChatProvider>
    </div>
  );
}

export default App;
