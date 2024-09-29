import { useEffect, useState } from 'react';
import { FiSend } from 'react-icons/fi';
import { useMutation } from 'react-query';
import httpClient from '../httpClient';


interface ChatMessage {
  id: number;
  content: string;
  reply_to: number | null;
  is_from_user: boolean;
  buttons: string[];
}

const Chat = () => {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState('');
  const [editMessageId, setEditMessageId] = useState<string | null>(
    null
  );
  const [editedContent, setEditedContent] = useState('');

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    try {
      const response = await httpClient.get('/messages/history');
      setChatHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch chat history');
    }
  };

  // Send message mutation
  const sendMessageMutation = useMutation(
    (newMessage: string) =>
      httpClient.post('/messages', { content: newMessage }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('chatHistory');
      },
    }
  );

  // Delete message mutation
  const deleteMessageMutation = useMutation(
    (messageId: string) =>
      httpClient.delete(`/messages/${messageId}`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('chatHistory');
      },
    }
  );

  // Edit message mutation
  const editMessageMutation = useMutation(
    ({
      messageId,
      content,
    }: {
      messageId: string;
      content: string;
    }) => httpClient.put(`/messages/${messageId}`, { content }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('chatHistory');
        setEditMessageId(null); // Reset edit mode
      },
    }
  );

  const handleSendMessage = () => {
    if (message.trim()) {
      sendMessageMutation.mutate(message);
      setMessage('');
    }
  };

  const handleDeleteMessage = (messageId: string) => {
    deleteMessageMutation.mutate(messageId);
  };

  const handleEditMessage = (messageId: string, content: string) => {
    setEditMessageId(messageId);
    setEditedContent(content);
  };

  const handleSaveEdit = (messageId: string) => {
    if (editedContent.trim()) {
      editMessageMutation.mutate({
        messageId,
        content: editedContent,
      });
    }
  };

  return (
    <div className="max-w-lg mx-auto max-h-screen bg-white shadow-lg rounded-lg flex flex-col">
      {/* Chat Header */}
      <div className="flex items-center p-4 border-b border-gray-200">
        <img
          src="https://randomuser.me/api/portraits/women/44.jpg"
          alt="Bot Avatar"
          className="w-12 h-12 rounded-full mr-3"
        />
        <div>
          <h2 className="text-xl font-semibold">Hey👋, I'm Ava</h2>
          <p className="text-sm text-gray-500">
            Ask me anything or pick a place to start
          </p>
        </div>
      </div>

      {/* Chat Body */}
      <div className="p-4 space-y-4 h-96 overflow-y-auto flex-1">
        {chatHistory?.map((chat: ChatMessage, index: number) => (
          <div
            key={index}
            className={`flex ${
              chat.is_from_user ? 'justify-end' : 'justify-start'
            } group`} // Added group class here
          >
            {/* Avatar for bot messages */}
            {!chat.is_from_user && (
              <img
                src="https://randomuser.me/api/portraits/women/44.jpg"
                alt="Bot Avatar"
                className="w-8 h-8 rounded-full mr-3 self-end"
              />
            )}

            <div
              className={`relative max-w-xs p-3 rounded-2xl ${
                chat.is_from_user
                  ? 'bg-purple-500 text-white rounded-br-none float-right'
                  : 'bg-gray-100 text-black rounded-bl-none float-left'
              }`}
            >
              {/* Message Content */}
              {editMessageId === chat.id.toString() ? (
                <div className="relative">
                  <input
                    type="text"
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="w-full p-2 border rounded text-black"
                  />
                  <button
                    className="mt-2 bg-blue-500 text-white p-2 rounded"
                    onClick={() => handleSaveEdit(chat.id.toString())}
                  >
                    Save
                  </button>
                </div>
              ) : (
                <>
                  <p className="font-normal text-sm break-words">
                    {chat.content}
                  </p>
                  {/* Optional bot buttons */}
                  {!chat.is_from_user &&
                    chat.buttons &&
                    chat.buttons.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {chat.buttons.map(
                          (buttonText: string, index: number) => (
                            <button
                              key={index}
                              className="border border-purple-500 text-purple-500 py-1 px-3 rounded-full hover:bg-purple-500 hover:text-white transition"
                            >
                              {buttonText}
                            </button>
                          )
                        )}
                      </div>
                    )}

                  {/* Edit/Delete buttons on user messages */}
                  {chat.is_from_user && (
                    <div className="absolute top-1 right-1 hidden group-hover:flex space-x-2">
                      {' '}
                      <button
                        className="text-xs bg-yellow-500 text-white p-1 rounded"
                        onClick={() =>
                          handleEditMessage(chat.id.toString(), chat.content)
                        }
                      >
                        Edit
                      </button>
                      <button
                        className="text-xs bg-red-500 text-white p-1 rounded"
                        onClick={() => handleDeleteMessage(chat.id.toString())}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* User Avatar */}
            {chat.is_from_user && (
              <img
                src="https://randomuser.me/api/portraits/men/45.jpg"
                alt="User Avatar"
                className="w-8 h-8 rounded-full ml-3 self-end"
              />
            )}
          </div>
        ))}
      </div>

      {/* Message Input Section */}
      <div className="flex items-center p-4 border-t border-gray-200">
        <img
          src="https://randomuser.me/api/portraits/men/45.jpg"
          alt="User Avatar"
          className="w-8 h-8 rounded-full mr-3"
        />
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Your question"
          className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <button
          onClick={handleSendMessage}
          className="ml-3 text-purple-500"
        >
          <FiSend className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};

export default Chat;
