import UIKit

@main @MainActor final class ProbeApp: UIResponder, UIApplicationDelegate {
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession,
                     options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config = UISceneConfiguration(name: "Probe", sessionRole: session.role)
        config.delegateClass = ProbeScene.self
        return config
    }
}

@MainActor final class ProbeScene: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let scene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: scene)
        window.overrideUserInterfaceStyle = .light
        window.rootViewController = ProbeController()
        self.window = window
        window.makeKeyAndVisible()
    }
}

@MainActor final class ProbeController: UIViewController {
    private let stack = UIStackView()
    private var didStart = false
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        stack.axis = .vertical; stack.spacing = 24; stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -24),
            stack.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 28)
        ])
        add("SYNTHETIC PRIVACY TEST", size: 16)
        add("Total Balance", size: 18)
        add("$1,259,301", size: 58)
        add("Recovery Phrase", size: 22)
        add("fixture one\nfixture two\nfixture three\nfixture four", size: 22)
        add("Private key (not a key)", size: 18)
        add("TEST-ONLY-NO-CREDENTIAL", size: 20)
    }
    private func add(_ text: String, size: CGFloat) {
        let label = UILabel();label.text = text;label.numberOfLines = 0
        label.font = .systemFont(ofSize: size, weight: .medium);label.textColor = .label
        stack.addArrangedSubview(label)
    }
    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        guard !didStart, let window = view.window else { return };didStart = true
        Task {
            do {
                try await Task.sleep(for: .seconds(1))
                try capture(window, name: "uncovered")
                let cover = OathAppSwitcherPrivacy(frame: window.bounds)
                window.addSubview(cover);cover.layoutIfNeeded()
                try await Task.sleep(for: .seconds(1))
                try capture(window, name: "covered-light")
                window.overrideUserInterfaceStyle = .dark
                cover.updateAppearance();cover.layoutIfNeeded()
                try await Task.sleep(for: .seconds(1))
                try capture(window, name: "covered-dark")
                let path = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                try Data("completed".utf8).write(to: path.appendingPathComponent("result.txt"))
            } catch {
                print("Synthetic privacy probe failed: \(type(of: error))")
            }
        }
    }
    private func capture(_ window: UIWindow, name: String) throws {
        let renderer = UIGraphicsImageRenderer(bounds: window.bounds)
        let image = renderer.image { _ in window.drawHierarchy(in: window.bounds, afterScreenUpdates: true) }
        guard let data = image.pngData() else { throw CocoaError(.fileWriteUnknown) }
        let path = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        try data.write(to: path.appendingPathComponent(name + ".png"))
    }
}
