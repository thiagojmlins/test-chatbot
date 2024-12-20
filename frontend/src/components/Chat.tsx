import { useEffect, useState } from 'react';
import { FiSend } from 'react-icons/fi';
import { useMutation, useQueryClient, useQuery } from 'react-query';
import httpClient from '../httpClient';

interface ChatMessage {
  id: number;
  content: string;
  reply_to: number | null;
  is_from_user: boolean;
  buttons: string[];
}

const Chat = () => {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState('');
  const [editMessageId, setEditMessageId] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState('');

  const { data: chatHistory, refetch: refetchChatHistory, isLoading, error } = useQuery(
    'chatHistory',
    () => httpClient.get('/messages/history').then((res) => res.data),
    { enabled: true }
  );

  useEffect(() => {
    refetchChatHistory();
  }, [refetchChatHistory]);

  const sendMessageMutation = useMutation(
    (content: string) => httpClient.post('/messages', { content }),
    {
      onSuccess: () => queryClient.invalidateQueries('chatHistory'),
    }
  );

  const deleteMessageMutation = useMutation(
    (messageId: string) => httpClient.delete(`/messages/${messageId}`),
    {
      onSuccess: () => queryClient.invalidateQueries('chatHistory'),
    }
  );

  const editMessageMutation = useMutation(
    ({ messageId, content }: { messageId: string; content: string }) =>
      httpClient.put(`/messages/${messageId}`, { content }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('chatHistory');
        setEditMessageId(null);
      },
    }
  );

  const handleSendMessage = () => {
    if (message.trim()) {
      sendMessageMutation.mutate(message);
      setMessage('');
    }
  };

  const handleDeleteMessage = (messageId: string) => deleteMessageMutation.mutate(messageId);

  const handleEditMessage = (messageId: string, content: string) => {
    setEditMessageId(messageId);
    setEditedContent(content);
  };

  const handleSaveEdit = (messageId: string) => {
    if (editedContent.trim()) {
      editMessageMutation.mutate({ messageId, content: editedContent });
    }
  };

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error while fetching chat history!</div>;

  return (
    <div className="max-w-lg mx-auto max-h-screen bg-white shadow-lg rounded-lg flex flex-col">
      <ChatHeader />
      <ChatBody
        chatHistory={chatHistory}
        editMessageId={editMessageId}
        editedContent={editedContent}
        setEditedContent={setEditedContent}
        handleSaveEdit={handleSaveEdit}
        handleEditMessage={handleEditMessage}
        handleDeleteMessage={handleDeleteMessage}
      />
      <MessageInput
        message={message}
        setMessage={setMessage}
        handleSendMessage={handleSendMessage}
      />
    </div>
  );
};

const ChatHeader = () => (
  <div className="flex items-center p-4 border-b border-gray-200">
    <img
      src="https://randomuser.me/api/portraits/women/44.jpg"
      alt="Bot Avatar"
      className="w-12 h-12 rounded-full mr-3"
    />
    <div>
      <h2 className="text-xl font-semibold">Hey👋, I'm Ava</h2>
      <p className="text-sm text-gray-500">Ask me anything or pick a place to start</p>
    </div>
  </div>
);

const ChatBody = ({
  chatHistory,
  editMessageId,
  editedContent,
  setEditedContent,
  handleSaveEdit,
  handleEditMessage,
  handleDeleteMessage,
}) => (
  <div className="p-4 space-y-4 h-96 overflow-y-auto flex-1">
    {chatHistory?.map((chat: ChatMessage, index: number) => (
      <ChatMessage
        key={index}
        chat={chat}
        editMessageId={editMessageId}
        editedContent={editedContent}
        setEditedContent={setEditedContent}
        handleSaveEdit={handleSaveEdit}
        handleEditMessage={handleEditMessage}
        handleDeleteMessage={handleDeleteMessage}
      />
    ))}
  </div>
);

const ChatMessage = ({
  chat,
  editMessageId,
  editedContent,
  setEditedContent,
  handleSaveEdit,
  handleEditMessage,
  handleDeleteMessage,
}) => (
  <div className={`flex ${chat.is_from_user ? 'justify-end' : 'justify-start'} group`}>
    {!chat.is_from_user && <BotAvatar />}
    <div
      className={`relative max-w-xs p-3 rounded-2xl ${
        chat.is_from_user
          ? 'bg-purple-500 text-white rounded-br-none float-right'
          : 'bg-gray-100 text-black rounded-bl-none float-left'
      }`}
    >
      {editMessageId === chat.id.toString() ? (
        <EditMessageForm
          editedContent={editedContent}
          setEditedContent={setEditedContent}
          handleSaveEdit={() => handleSaveEdit(chat.id.toString())}
        />
      ) : (
        <MessageContent
          chat={chat}
          handleEditMessage={handleEditMessage}
          handleDeleteMessage={handleDeleteMessage}
        />
      )}
    </div>
    {chat.is_from_user && <UserAvatar />}
  </div>
);

const BotAvatar = () => (
  <img
    src="https://randomuser.me/api/portraits/women/44.jpg"
    alt="Bot Avatar"
    className="w-8 h-8 rounded-full mr-3 self-end"
  />
);

const UserAvatar = () => (
  <img
    src="https://randomuser.me/api/portraits/men/45.jpg"
    alt="User Avatar"
    className="w-8 h-8 rounded-full ml-3 self-end"
  />
);

interface EditMessageFormProps {
  editedContent: string;
  setEditedContent: (content: string) => void;
  handleSaveEdit: () => void;
}

const EditMessageForm: React.FC<EditMessageFormProps> = ({ editedContent, setEditedContent, handleSaveEdit }) => (
  <div className="relative">
    <input
      type="text"
      value={editedContent}
      onChange={(e) => setEditedContent(e.target.value)}
      className="w-full p-2 border rounded text-black"
      data-testid="edit-message-input"
    />
    <button
      className="mt-2 bg-blue-500 text-white p-2 rounded"
      onClick={handleSaveEdit}
    >
      Save
    </button>
  </div>
);

const MessageContent = ({ chat, handleEditMessage, handleDeleteMessage }) => (
  <>
    <p className="font-normal text-sm break-words">{chat.content}</p>
    {!chat.is_from_user && chat.buttons && chat.buttons.length > 0 && (
      <div className="mt-2 space-y-2">
        {chat.buttons.map((buttonText: string, index: number) => (
          <button
            key={index}
            className="border border-purple-500 text-purple-500 py-1 px-3 rounded-full hover:bg-purple-500 hover:text-white transition"
          >
            {buttonText}
          </button>
        ))}
      </div>
    )}
    {chat.is_from_user && (
      <div className="absolute top-1 right-1 hidden group-hover:flex space-x-2">
        <button
          className="text-xs bg-yellow-500 text-white p-1 rounded"
          onClick={() => handleEditMessage(chat.id.toString(), chat.content)}
          data-testid="edit-button"
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
);

interface MessageInputProps {
  message: string;
  setMessage: (message: string) => void;
  handleSendMessage: () => void;
}

const MessageInput: React.FC<MessageInputProps> = ({ message, setMessage, handleSendMessage }) => (
  <div className="flex items-center p-4 border-t border-gray-200">
    <UserAvatar />
    <input
      type="text"
      value={message}
      onChange={(e) => setMessage(e.target.value)}
      placeholder="Your question"
      className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
      data-testid="new-message-input"
    />
    <button
      onClick={handleSendMessage}
      className="ml-3 text-purple-500"
      data-testid="send-button"
    >
      <FiSend className="w-6 h-6" />
    </button>
  </div>
);

export default Chat;
