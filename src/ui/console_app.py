import requests
import uuid
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Style
import textwrap

init()

mock_suggestions = {'concept_text': 'Washington', 'options': [
    {'filter_id': '1', 'filter_name': 'City', 'operator': 'EQUAL', 'value': 'Washington D.C.'},
    {'filter_id': '1', 'filter_name': 'State', 'operator': 'EQUAL', 'value': 'Washington'},
]}

class ConsoleFilterAssistant:
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url
        self.active_filters = []
        self.clarification_request = []
        self.chat_history = []
        self.session_id = str(uuid.uuid4())

    def display_banner(self):
        """Display welcome banner"""
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.CYAN}🤖 Filter Assistant - Console Mode")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Commands:")
        print(f"  - Type your query to search for clients")
        print(f"  - Type 'filters' to see current filters")
        print(f"  - Type 'clear' to clear all filters")
        print(f"  - Type 'history' to see chat history")
        print(f"  - Type a number (1-9) to select a suggestion")
        print(f"  - Type 'help' for this message")
        print(f"  - Type 'exit' or 'quit' to exit{Style.RESET_ALL}\n")

    def display_filters(self):
        """Display current filters in a formatted way"""
        if not self.active_filters:
            print(f"{Fore.YELLOW}No filters currently applied.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.GREEN}📋 Active Filters:{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'─' * 40}{Style.RESET_ALL}")

        for i, filter_item in enumerate(self.active_filters, 1):
            filter_name = filter_item.get('filter_name', 'Unknown')
            operator = filter_item.get('operator', '=')
            value = filter_item.get('value', '')

            operator_display = {
                '>': 'greater than',
                '<': 'less than',
                '>=': 'at least',
                '<=': 'at most',
                '=': 'equals',
                'between': 'between',
                'within': 'within last'
            }.get(operator, operator)

            print(f"{Fore.CYAN}{i}. {filter_name}:{Style.RESET_ALL}")
            print(f"   {operator_display} {value}")

        print(f"{Fore.GREEN}{'─' * 40}{Style.RESET_ALL}\n")

    def display_suggestions(self):
        """Display pending suggestions"""
        if not self.clarification_request:
            return

        print(f"\n{Fore.YELLOW}💡 I need clarification:{Style.RESET_ALL}")

        option_num = 1
        for suggestion in self.clarification_request:
            concept = suggestion.get('concept_text', 'your input')
            print(f"\n{Fore.YELLOW}For '{concept}':{Style.RESET_ALL}")

            for option in suggestion.get('options', []):
                filter_name = option.get('filter_name', 'Unknown')
                operator = option.get('operator', '')
                value = option.get('value', '')

                display_text = f"{filter_name} {operator} '{value}'"

                print(f"  {Fore.CYAN}{option_num}{Style.RESET_ALL}. {display_text}")
                option_num += 1

        print(f"\n{Fore.YELLOW}Type the number to apply a suggestion{Style.RESET_ALL}")

    def apply_suggestion(self, selection: int) -> bool:
        """Apply a selected suggestion"""
        if not self.clarification_request:
            return False

        all_options = []
        for suggestion in self.clarification_request:
            all_options.extend(suggestion.get('options', []))

        if selection < 1 or selection > len(all_options):
            return False

        selected_option = all_options[selection - 1]

        new_filter = {
            'filter_id': selected_option['filter_id'],
            'filter_name': selected_option['filter_name'],
            'operator': selected_option['operator'],
            'value': selected_option['value']
        }
        self.active_filters.append(new_filter)

        display_text = f"{selected_option['filter_name']} {selected_option['operator']} '{selected_option['value']}'"
        print(f"{Fore.GREEN}✓ Applied filter: {display_text}{Style.RESET_ALL}")

        self.clarification_request = []

        return True

    def process_query(self, query: str) -> Dict[str, Any]:
        """Send query to API and get response"""
        try:
            request_data = {
                "query": query,
                "active_filters": self.active_filters,
                "session_id": self.session_id
            }

            response = requests.post(
                f"{self.api_url}/api/chat",
                json=request_data,
                timeout=None
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API error: {response.status_code}",
                    "message": "Failed to process query"
                }

        except requests.exceptions.ConnectionError:
            return {
                "error": "Cannot connect to API server",
                "message": "Make sure the Flask server is running on port 5000"
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": "An error occurred"
            }

    def display_response(self, response: Dict[str, Any]):
        """Display API response in a formatted way"""
        if response.get("error"):
            print(f"{Fore.RED}❌ Error: {response['error']}{Style.RESET_ALL}")
            return

        if response.get("session_id"):
            self.session_id = response["session_id"]

        message = response.get("message", "Query processed")
        print(f"\n{Fore.BLUE}🤖 Assistant:{Style.RESET_ALL}")
        wrapped_message = textwrap.fill(message, width=60)
        print(f"{wrapped_message}")

        new_filters = response.get("active_filters", [])
        filters_changed = False

        if new_filters != self.active_filters:
            added = len(new_filters) - len(self.active_filters)
            if added > 0:
                print(f"{Fore.GREEN}✅ Added {added} filter(s){Style.RESET_ALL}")
            elif added < 0:
                print(f"{Fore.YELLOW}✅ Removed {-added} filter(s){Style.RESET_ALL}")
            else:
                print(f"{Fore.BLUE}✅ Modified filter(s){Style.RESET_ALL}")

            self.active_filters = new_filters
            filters_changed = True

        self.clarification_request = response.get("clarification_request", [])

        if filters_changed and self.active_filters:
            self.display_filters()

        if self.clarification_request:
            self.display_suggestions()

    def display_history(self):
        """Display chat history"""
        if not self.chat_history:
            print(f"{Fore.YELLOW}No chat history yet.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}📜 Chat History:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")

        for entry in self.chat_history:
            print(f"{Fore.GREEN}You:{Style.RESET_ALL} {entry['user']}")
            print(f"{Fore.BLUE}Bot:{Style.RESET_ALL} {entry['bot']}")
            print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")

    def run(self):
        """Main console loop"""
        self.display_banner()

        while True:
            try:
                prompt = f"{Fore.GREEN}You > {Style.RESET_ALL}"
                if self.clarification_request:
                    total_options = sum(len(s.get('options', [])) for s in self.clarification_request)
                    prompt = f"{Fore.YELLOW}[{total_options} pending] {prompt}"

                user_input = input(prompt).strip()

                if user_input.lower() in ['exit', 'quit']:
                    print(f"{Fore.YELLOW}Goodbye! 👋{Style.RESET_ALL}")
                    break

                elif user_input.lower() == 'help':
                    self.display_banner()
                    continue

                elif user_input.lower() == 'filters':
                    self.display_filters()
                    continue

                elif user_input.lower() == 'clear':
                    self.active_filters = []
                    self.clarification_request = []
                    print(f"{Fore.GREEN}✅ All filters cleared!{Style.RESET_ALL}")
                    continue

                elif user_input.lower() == 'history':
                    self.display_history()
                    continue

                elif not user_input:
                    continue

                if user_input.isdigit() and self.clarification_request:
                    selection = int(user_input)
                    if self.apply_suggestion(selection):
                        continue
                    else:
                        print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
                        continue

                print(f"{Fore.YELLOW}Processing...{Style.RESET_ALL}")
                response = self.process_query(user_input)

                self.display_response(response)

                self.chat_history.append({
                    'user': user_input,
                    'bot': response.get('message', 'No response')
                })

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use 'exit' or 'quit' to leave.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                import traceback
                traceback.print_exc()


def run_console_app(api_url: str = "http://localhost:5000"):
    """Run the console application"""
    app = ConsoleFilterAssistant(api_url)
    app.run()