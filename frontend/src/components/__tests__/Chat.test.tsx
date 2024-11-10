import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { describe, it, beforeEach, vi, expect } from 'vitest';
import httpClient from '../../httpClient';
import Chat from '../Chat';

// Mock the httpClient
vi.mock('../../httpClient');

// Mock data
const mockChatHistory = [
  {
    id: 1,
    content: "Hello!",
    reply_to: null,
    is_from_user: true,
    buttons: []
  },
  {
    id: 2,
    content: "Hi there! How can I help?",
    reply_to: 1,
    is_from_user: false,
    buttons: ["Option 1", "Option 2"]
  }
];

describe('Chat Component', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    // Reset all mocks before each test
    vi.clearAllMocks();
    // Setup default successful responses
    vi.mocked(httpClient.get).mockResolvedValue({ data: mockChatHistory });
  });

  const renderChat = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <Chat />
      </QueryClientProvider>
    );
  };

  it('renders loading state initially', () => {
    renderChat();
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('renders chat history after loading', async () => {
    renderChat();
    await waitFor(() => {
      expect(screen.getByText('Hello!')).toBeDefined();
      expect(screen.getByText('Hi there! How can I help?')).toBeDefined();
    });
  });

  it('sends a new message', async () => {
    vi.mocked(httpClient.post).mockResolvedValueOnce({ data: { success: true } });

    renderChat();

    // Wait for the chat to load first
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).toBeNull();
    });

    // Find input by its role and send button
    const input = screen.getByRole('textbox');
    const sendButton = screen.getByTestId('send-button');

    await act(async () => {
      fireEvent.change(input, { target: { value: 'New message' } });
      fireEvent.click(sendButton);
    });

    expect(httpClient.post).toHaveBeenCalledWith('/messages', {
      content: 'New message'
    });
  });

  it('deletes a message', async () => {
    vi.mocked(httpClient.delete).mockResolvedValueOnce({ data: { success: true } });

    renderChat();

    await waitFor(() => {
      const deleteButton = screen.getAllByText('Delete')[0];
      fireEvent.click(deleteButton);
    });

    expect(httpClient.delete).toHaveBeenCalledWith('/messages/1');
  });

  it('edits a message', async () => {
    vi.mocked(httpClient.put).mockResolvedValueOnce({ data: { success: true } });

    renderChat();

    // Wait for chat history to load
    await waitFor(() => {
      expect(screen.queryByText('Hello!')).toBeDefined();
    });

    // Find and click the edit button
    const editButton = screen.getByTestId('edit-button');
    await waitFor(() => {
      fireEvent.click(editButton);
    });

    // Find edit input and change its value
    const editInput = screen.getByTestId('edit-message-input');
    await waitFor(() => {
      fireEvent.change(editInput, { target: { value: 'Edited message' } });
    });

    // Click save button
    const saveButton = screen.getByText('Save');
    await waitFor(() => {
      fireEvent.click(saveButton);
    });

    // Wait for the PUT request to be called
    await waitFor(() => {
      expect(httpClient.put).toHaveBeenCalledWith('/messages/1', {
        content: 'Edited message'
      });
    });
  });

  it('renders error state when fetch fails', async () => {
    vi.mocked(httpClient.get).mockRejectedValueOnce(new Error('Failed to fetch'));

    renderChat();

    await waitFor(() => {
      expect(screen.getByText('Error while fetching chat history!')).toBeDefined();
    });
  });

  it('renders bot buttons when present', async () => {
    renderChat();

    await waitFor(() => {
      expect(screen.getByText('Option 1')).toBeDefined();
      expect(screen.getByText('Option 2')).toBeDefined();
    });
  });
});
