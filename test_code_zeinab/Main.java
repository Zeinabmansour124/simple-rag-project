package org.example;

import org.example.dao.*;
import org.example.model.Admin;
import org.example.model.Customer;
import org.example.model.Transaction;
import org.example.ui.LoginFrame;


import javax.swing.*;
import java.util.List;
import java.util.Scanner;

public class Main {
    static Scanner scanner = new Scanner(System.in);
    static CustomerDAO customerDAO = new CustomerDAO();

    public static void main(String[] args) {
        SwingUtilities.invokeLater(LoginFrame::new);
        while (true) {
            System.out.println("\n===== Online Banking: Main Menu =====");
            System.out.println("1. Register");
            System.out.println("2. Login");
            System.out.println("3. Admin Login");
            System.out.println("4. Exit");
            System.out.print("Choose: ");
            int choice = scanner.nextInt();
            scanner.nextLine();

            switch (choice) {
                case 1 -> register();
                case 2 -> login();
                case 3 -> adminLogin();
                case 4 -> {
                    System.out.println("Exiting app. Goodbye!");
                    return;
                }
                default -> System.out.println("Invalid choice ❗");
            }
        }
    }

    private static void register() {
        System.out.println("\n-- Register New Customer --");
        System.out.print("Name: ");
        String name = scanner.nextLine();
        System.out.print("Email: ");
        String email = scanner.nextLine();
        System.out.print("Phone: ");
        String phone = scanner.nextLine();
        System.out.print("Password: ");
        String password = scanner.nextLine();

        Customer customer = new Customer(name, email, phone, password);
        boolean success = customerDAO.register(customer);
        System.out.println(success ? "✅ Registration successful!" : "❌ Registration failed.");
    }

    private static void login() {
        System.out.println("\n-- Customer Login --");
        System.out.print("Email: ");
        String email = scanner.nextLine();
        System.out.print("Password: ");
        String password = scanner.nextLine();

        Customer customer = customerDAO.login(email, password);
        if (customer != null) {
            System.out.println("✅ Welcome, " + customer.getName() + "!");
            customerDashboard(customer);
        } else {
            System.out.println("❌ Invalid login credentials.");
        }
    }

    private static void adminLogin() {
        AdminDAO adminDAO = new AdminDAO();
        Scanner sc = new Scanner(System.in);
        System.out.print("Username: ");
        String username = sc.nextLine();
        System.out.print("Password: ");
        String password = sc.nextLine();

        Admin admin = adminDAO.login(username, password);
        if (admin != null) {
            System.out.println("✅ Admin access granted. Welcome " + admin.getUsername());
            adminDashboard();
        } else {
            System.out.println("❌ Invalid admin credentials.");
        }
    }

    private static void adminDashboard() {
        Scanner sc = new Scanner(System.in);
        AdminService service = new AdminService();
        InterestService interest = new InterestService();

        while (true) {
            System.out.println("\n===== ADMIN PANEL =====");
            System.out.println("1. View All Customers");
            System.out.println("2. View All Transactions");
            System.out.println("3. Apply Monthly Interest");
            System.out.println("4. Exit Admin Panel");
            System.out.print("Choose: ");
            int choice = sc.nextInt();

            switch (choice) {
                case 1 -> {
                    var customers = service.getAllCustomers();
                    System.out.println("--- Customers ---");
                    for (var c : customers)
                        System.out.printf("ID: %d | Name: %s | Email: %s | Phone: %s%n",
                                c.getCustomerId(), c.getName(), c.getEmail(), c.getPhone());
                }
                case 2 -> {
                    var txns = service.getAllTransactions();
                    System.out.println("--- Transactions ---");
                    for (var t : txns)
                        System.out.printf("[%s] %s $%.2f | From: %d → To: %d | CustID: %d%n",
                                t.getDate(), t.getType(), t.getAmount(), t.getFromAccount(), t.getToAccount(), t.getCustomerId());
                }
                case 3 -> {
                    boolean applied = interest.applyMonthlyInterest();
                    System.out.println(applied ? "✅ Interest applied to savings accounts." : "❌ Failed to apply interest.");
                }
                case 4 -> {
                    System.out.println("Returning to main menu...");
                    return;
                }
                default -> System.out.println("Invalid choice ❗");
            }
        }
    }

    private static void customerDashboard(Customer customer) {
        AccountDAO accountDAO = new AccountDAO();

        while (true) {
            System.out.println("\n===== Welcome, " + customer.getName() + " =====");
            System.out.println("1. Open Checking Account");
            System.out.println("2. Open Savings Account");
            System.out.println("3. View Accounts");
            System.out.println("4. Deposit");
            System.out.println("5. Withdraw");
            System.out.println("6. Transfer");
            System.out.println("7. View Transactions");
            System.out.println("8. Logout");
            System.out.print("Choose: ");
            int choice = scanner.nextInt();
            scanner.nextLine();

            switch (choice) {
                case 1 -> {
                    if (accountDAO.createCheckingAccount(customer.getCustomerId()))
                        System.out.println("✅ Checking account created.");
                    else
                        System.out.println("❌ Could not create checking account.");
                }
                case 2 -> {
                    if (accountDAO.createSavingsAccount(customer.getCustomerId()))
                        System.out.println("✅ Savings account created.");
                    else
                        System.out.println("❌ Could not create savings account.");
                }
                case 3 -> {
                    var checking = accountDAO.getCheckingAccount(customer.getCustomerId());
                    var savings = accountDAO.getSavingsAccount(customer.getCustomerId());

                    if (checking != null)
                        System.out.printf("🔹 Checking Account: #%d | Balance: $%.2f%n", checking.getAccountNumber(), checking.getBalance());
                    else
                        System.out.println("No Checking Account.");

                    if (savings != null)
                        System.out.printf("🔹 Savings Account: #%d | Balance: $%.2f | Interest: %.2f%%%n",
                                savings.getAccountNumber(), savings.getBalance(), savings.getInterestRate());
                    else
                        System.out.println("No Savings Account.");
                }
                case 4 -> {
                    System.out.print("Enter checking account number: ");
                    int acc = scanner.nextInt();
                    System.out.print("Enter amount to deposit: ");
                    double amt = scanner.nextDouble();
                    boolean success = new TransactionDAO().deposit(acc, amt, customer.getCustomerId(), "Deposit");
                    System.out.println(success ? "Deposit successful ✔️" : "❌ Deposit failed.");
                }

                case 5 -> {
                    System.out.print("Enter checking account number: ");
                    int acc = scanner.nextInt();
                    System.out.print("Enter amount to withdraw: ");
                    double amt = scanner.nextDouble();
                    boolean success = new TransactionDAO().withdraw(acc, amt, customer.getCustomerId());
                    System.out.println(success ? "Withdrawal successful ✔️" : "❌ Insufficient balance or failed.");
                }

                case 6 -> {
                    System.out.print("Enter FROM account number: ");
                    int from = scanner.nextInt();
                    System.out.print("Enter TO account number: ");
                    int to = scanner.nextInt();
                    System.out.print("Enter amount to transfer: ");
                    double amt = scanner.nextDouble();
                    boolean success = new TransactionDAO().transfer(from, to, amt, customer.getCustomerId());
                    System.out.println(success ? "Transfer complete ✔️" : "❌ Transfer failed.");
                }

                case 7 -> {
                    List<Transaction> txns = new TransactionDAO().getTransactions(customer.getCustomerId());
                    if (txns.isEmpty()) System.out.println("No transactions found.");
                    for (Transaction t : txns) {
                        System.out.printf("[%s] %s $%.2f | From: %d -> To: %d%n",
                                t.getDate(), t.getType(), t.getAmount(), t.getFromAccount(), t.getToAccount());
                    }
                }

                case 8 -> {
                    System.out.println("Logging out...");
                    return;
                }
                default -> System.out.println("❌ Invalid option.");
            }
        }
    }
}
